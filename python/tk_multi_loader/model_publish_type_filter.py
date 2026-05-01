import sgtk
from sgtk.platform.qt import QtCore, QtGui

shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_model"
)
ShotgunModel = shotgun_model.ShotgunModel


class SgPublishTypeFilterModel(ShotgunModel):

    SORT_KEY_ROLE = QtCore.Qt.UserRole + 102
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 103

    FOLDERS_ITEM_TEXT = "Folders"

    def __init__(self, parent, settings_manager, bg_task_manager):
        super(SgPublishTypeFilterModel, self).__init__(
            parent,
            download_thumbs=False,
            schema_generation=2,
            bg_load_thumbs=True,
            bg_task_manager=bg_task_manager,
        )

        self._settings_manager = settings_manager
        self.setSortRole(self.SORT_KEY_ROLE)

        # restore deselected state
        self._deselected_pub_types = self._settings_manager.retrieve(
            "deselected_pub_types_custom", [], self._settings_manager.SCOPE_INSTANCE
        )

        ShotgunModel._load_data(
            self,
            entity_type="CustomNonProjectEntity06",
            filters=[],
            hierarchy=["code"],
            fields=["code", "id"],
        )

        self._refresh_data()

    def destroy(self):
        val = []
        for idx in range(self.rowCount()):
            item = self.item(idx)
            if item.checkState() == QtCore.Qt.Unchecked:
                sg_data = shotgun_model.get_sg_data(item)
                if sg_data:
                    val.append(sg_data.get("code"))

        self._settings_manager.store(
            "deselected_pub_types_custom",
            val,
            self._settings_manager.SCOPE_INSTANCE,
        )

        super(SgPublishTypeFilterModel, self).destroy()

    def select_none(self):
        for idx in range(self.rowCount()):
            item = self.item(idx)
            if item.text() != self.FOLDERS_ITEM_TEXT:
                item.setCheckState(QtCore.Qt.Unchecked)

    def select_all(self):
        for idx in range(self.rowCount()):
            item = self.item(idx)
            item.setCheckState(QtCore.Qt.Checked)

    def get_show_folders(self):
        for idx in range(self.rowCount()):
            item = self.item(idx)
            if item.text() == self.FOLDERS_ITEM_TEXT:
                return item.checkState() == QtCore.Qt.Checked
        return False

    def get_selected_types(self):
        type_ids = []
        for idx in range(self.rowCount()):
            item = self.item(idx)

            if item.text() == self.FOLDERS_ITEM_TEXT:
                continue

            if item.checkState() == QtCore.Qt.Checked:
                type_ids.append(item.get_sg_data()["id"])

        return type_ids

    def set_active_types(self, type_aggregates):
        for idx in range(self.rowCount()):
            item = self.item(idx)

            if item.text() == self.FOLDERS_ITEM_TEXT:
                continue

            sg_data = shotgun_model.get_sg_data(item)
            type_id = sg_data["id"]

            display_name = shotgun_model.get_sanitized_data(
                item, self.DISPLAY_NAME_ROLE
            )

            total_matches = type_aggregates.get(type_id, 0)

            if total_matches > 0:
                item.setEnabled(True)
                item.setData(f"a_{display_name}", self.SORT_KEY_ROLE)
                item.setText(f"{display_name} ({total_matches})")
            else:
                item.setEnabled(False)
                item.setData(f"b_{display_name}", self.SORT_KEY_ROLE)
                item.setText(f"{display_name} (0)")

        self.sort(0)

    def hard_refresh(self):
        super(SgPublishTypeFilterModel, self).hard_refresh()
        self._load_external_data()


    def _load_external_data(self):
        self._folder_items = []

        item = shotgun_model.ShotgunStandardItem(self.FOLDERS_ITEM_TEXT)
        item.setCheckable(True)
        item.setCheckState(QtCore.Qt.Checked)
        item.setToolTip("Toggle folder visibility")

        self.appendRow(item)
        self._folder_items.append(item)

    def _finalize_item(self, item):
        item.setEnabled(False)

        sg_data = item.get_sg_data()
        if sg_data and sg_data.get("code") not in self._deselected_pub_types:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)

    def _populate_item(self, item, sg_data):
        name = sg_data.get("code") or "Unnamed"

        item.setData(name, self.DISPLAY_NAME_ROLE)
        item.setCheckable(True)