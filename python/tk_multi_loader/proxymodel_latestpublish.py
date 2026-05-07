# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import six

from .model_latestpublish import SgLatestPublishModel

shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_model"
)


class SgLatestPublishProxyModel(QtGui.QSortFilterProxyModel):
    """
    Filter model to be used in conjunction with SgLatestPublishModel
    """

    # sort mode constants
    SORT_DATE_LATEST = 0
    SORT_DATE_OLDEST = 1
    SORT_NAME_AZ = 2
    SORT_NAME_ZA = 3
    SORT_VERSION_HIGH = 4
    SORT_VERSION_LOW = 5

    # signal which is emitted whenever a filter changes
    filter_changed = QtCore.Signal()

    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self._valid_type_ids = None
        self._show_folders = True
        self._search_filter = ""
        self._valid_sg_publish_type_ids = None
        self._sort_mode = self.SORT_DATE_LATEST

    def set_sort_mode(self, mode):
        """
        Set the sort mode and resort the view.
        """
        self._sort_mode = mode
        self.invalidate()
        self.filter_changed.emit()

    def set_search_query(self, search_filter):
        """
        Specify a filter to use for searching

        :param search_filter: search filter string
        """
        self._search_filter = search_filter
        self.invalidateFilter()
        self.filter_changed.emit()

    def set_filter_by_type_ids(self, type_ids, show_folders):
        """
        Specify which type ids the publish model should allow through
        """
        self._valid_type_ids = type_ids
        self._show_folders = show_folders
        # tell model to repush data
        self.invalidateFilter()
        self.filter_changed.emit()

    def set_filter_by_sg_publish_type_ids(self, type_ids):
        """
        Specify which Publish Type (CustomNonProjectEntity06) IDs to filter via the sg_publish_type field.
        """
        self._valid_sg_publish_type_ids = type_ids if type_ids else None
        self.invalidateFilter()
        self.filter_changed.emit()
    
    def lessThan(self, left_idx, right_idx):
        """
        Drives the sort order.
        """
        model = self.sourceModel()
        left_item = model.invisibleRootItem().child(left_idx.row())
        right_item = model.invisibleRootItem().child(right_idx.row())

        if left_item is None or right_item is None:
            return False

        # folders always sort above publishes
        left_is_folder  = left_item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        right_is_folder = right_item.data(SgLatestPublishModel.IS_FOLDER_ROLE)

        if left_is_folder and not right_is_folder:
            return True
        if not left_is_folder and right_is_folder:
            return False

        left_sg  = shotgun_model.get_sg_data(left_idx)
        right_sg = shotgun_model.get_sg_data(right_idx)

        if left_sg is None or right_sg is None:
            return False

        if self._sort_mode == self.SORT_DATE_LATEST:
            return (left_sg.get("created_at") or 0) > (right_sg.get("created_at") or 0)

        elif self._sort_mode == self.SORT_DATE_OLDEST:
            return (left_sg.get("created_at") or 0) < (right_sg.get("created_at") or 0)

        elif self._sort_mode == self.SORT_NAME_AZ:
            return (left_sg.get("name") or "").lower() < (right_sg.get("name") or "").lower()

        elif self._sort_mode == self.SORT_NAME_ZA:
            return (left_sg.get("name") or "").lower() > (right_sg.get("name") or "").lower()

        elif self._sort_mode == self.SORT_VERSION_HIGH:
            return (left_sg.get("version_number") or 0) > (right_sg.get("version_number") or 0)

        elif self._sort_mode == self.SORT_VERSION_LOW:
            return (left_sg.get("version_number") or 0) < (right_sg.get("version_number") or 0)

        return False

    def filterAcceptsRow(self, source_row, source_parent_idx):
        """
        Overridden from base class.

        This will check each row as it is passing through the proxy
        model and see if we should let it pass or not.
        """

        if self._valid_type_ids is None and self._valid_sg_publish_type_ids is None:
            # accept all!
            return True

        model = self.sourceModel()

        current_item = model.invisibleRootItem().child(
            source_row
        )  # assume non-tree structure

        # first analyze any search filtering
        if self._search_filter:

            # there is a search filter entered
            field_data = shotgun_model.get_sanitized_data(
                current_item, SgLatestPublishModel.SEARCHABLE_NAME
            )

            # all input we are getting from pyside is as unicode objects
            # all data from shotgun is utf-8. By converting to utf-8,
            # filtering on items containing unicode text also work.
            search_str = six.ensure_str(self._search_filter)

            if search_str.lower() not in field_data.lower():
                # item text is not matching search filter
                return False

        # now check if folders should be shown
        is_folder = current_item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        if is_folder:
            return self._show_folders

        # PublishedFileType filter
        if self._valid_type_ids is not None:
            sg_type_id = current_item.data(SgLatestPublishModel.TYPE_ID_ROLE)
            if sg_type_id is not None and sg_type_id not in self._valid_type_ids:
                return False

        # sg_publish_type filter 
        if self._valid_sg_publish_type_ids is not None:
            sg_publish_type_id = current_item.data(
                SgLatestPublishModel.SG_PUBLISH_TYPE_ID_ROLE
            )
            if sg_publish_type_id not in self._valid_sg_publish_type_ids:
                return False

        return True
