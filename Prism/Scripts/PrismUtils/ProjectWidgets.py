# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


import os
import sys
import copy
import re

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils import PrismWidgets
from PrismUtils.Decorators import err_catcher

from UserInterfacesPrism import CreateProject_ui


class CreateProject(QDialog, CreateProject_ui.Ui_dlg_createProject):
    def __init__(self, core, name=None, path=None, settings=None, enforcedSettings=None):
        QDialog.__init__(self)
        self.core = core
        self.prevName = ""
        self.projectSettings = {}
        self.enforcedSettings = enforcedSettings
        if self.core.uiAvailable:
            self.loadLayout()
            if name:
                self.e_name.setText(name)

            if path:
                self.e_path.setText(path)

            if settings:
                self.settingsApplied(settings)
            elif enforcedSettings:
                self.settingsApplied(None)

        self.enableCleanup = True
        self.core.callback(
            name="onCreateProjectOpen",
            args=[self],
        )
        path = os.path.join(self.core.prismRoot, "Scripts", "UserInterfacesPrism", "background.png")
        self.background = QPixmap(path)

    def paintEvent(self, event):
        pixmap = self.core.media.scalePixmap(self.background, self.width(), self.height(), fitIntoBounds=False)
        painter = QPainter(self)
        painter.setOpacity(0.3)
        painter.drawPixmap(0, 0, pixmap)

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.setupUi(self)
        self.core.parentWindow(self)
        self.sw_project.setStyleSheet("QStackedWidget { background-color: transparent;}")
        self.w_settings = QWidget()
        self.lo_settings = QHBoxLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 0, 0, 0)

        self.l_settings = QLabel("Settings:")
        self.cb_settings = QComboBox()
        self.cb_settings.addItems(["Default", "From Preset", "From Project"])
        self.cb_settings.currentIndexChanged.connect(self.onSettingsSourceChanged)
        self.lo_settings.addStretch()
        self.lo_settings.addWidget(self.cb_settings)
        self.lo_settings.addWidget(self.b_reload)

        self.w_start.layout().addWidget(self.l_settings, 2, 0)
        self.w_start.layout().addWidget(self.w_settings, 2, 1)

        self.l_projectSettings = QLabel("Project Settings:")
        self.e_projectSettings = QLineEdit()
        self.e_projectSettings.setText(getattr(self.core, "projectPath", ""))
        self.b_projectSettings = QToolButton()
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "browse.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_projectSettings.setIcon(icon)

        self.w_start.layout().addWidget(self.l_projectSettings, 4, 0)
        self.w_start.layout().addWidget(self.e_projectSettings, 4, 1)
        self.w_start.layout().addWidget(self.b_projectSettings, 4, 2)

        getattr(self.core.appPlugin, "createProject_startup", lambda x: None)(self)

        nameTT = "The name of the new project.\nThe project name will be visible at different locations in the Prism user interface."
        self.l_name.setToolTip(nameTT)
        self.e_name.setToolTip(nameTT)
        pathTT = "This is the directory, where the project will be saved.\nThis folder should be empty or should not exist.\nThe project name will NOT be appended automatically to this path."
        self.l_path.setToolTip(pathTT)
        self.e_path.setToolTip(pathTT)
        self.b_browse.setToolTip("Select a folder on the current PC")
        self.tw_structure.setToolTip("Rightclick to add, remove or rename folders")

        self.connectEvents()
        self.e_name.setFocus()

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "browse.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_browse.setIcon(icon)

        imgFile = os.path.join(
            self.core.prismRoot,
            "Presets/Projects/Default/00_Pipeline/Fallbacks/noFileBig.jpg",
        )
        pmap = self.core.media.getPixmapFromPath(imgFile)
        if pmap:
            self.l_preview.setMinimumSize(pmap.width(), pmap.height())
            self.l_preview.setPixmap(pmap)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "refresh.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_reload.setIcon(icon)
        self.b_reload.setToolTip("Restore Settings")

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_addPreset.setIcon(icon)
        self.b_addPreset.setToolTip("Create new preset from current settings")

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "configure.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_managePresets.setIcon(icon)
        self.b_managePresets.setToolTip("Manage Presets")

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "arrow_right.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_next.setIcon(icon)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "arrow_left.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_back.setIcon(icon)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_create.setIcon(icon)

        if self.sw_project.currentIndex() == 0:
            self.b_back.setVisible(False)

        presets = self.core.projects.getPresets()
        self.cb_preset.addItems([p["name"] for p in presets])
        self.reloadSettings()

        self.tw_structure.setHeaderLabel("Folder Structure")

        # self.lo_summary = QVBoxLayout()
        # self.w_summary.setLayout(self.lo_summary)

        self.w_complete = QWidget()
        self.lo_complete = QVBoxLayout(self.w_complete)
        self.l_complete = QLabel("Project <b>%s</b> was created successfully!")
        self.l_complete.setAlignment(Qt.AlignCenter)
        self.l_completeIcon = QLabel()
        headerPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "check.png"
        )
        icon = self.core.media.getColoredIcon(headerPath, r=29, g=191, b=106, force=True)
        self.l_completeIcon.setPixmap(icon.pixmap(60, 60))
        self.l_completeIcon.setAlignment(Qt.AlignCenter)
        self.w_completeButtons = QWidget()
        self.lo_completeButtons = QHBoxLayout(self.w_completeButtons)
        self.b_completeBrowser = QPushButton("Open Project Browser")
        self.b_completeBrowser.clicked.connect(self.core.projectBrowser)
        self.b_completeBrowser.clicked.connect(self.accept)
        self.b_completeExplorer = QPushButton("Open in Explorer")
        self.b_completeExplorer.clicked.connect(lambda: self.core.openFolder(self.core.projectPath))
        self.b_completeExplorer.clicked.connect(self.accept)
        self.lo_completeButtons.addStretch()
        self.lo_completeButtons.addWidget(self.b_completeBrowser)
        self.lo_completeButtons.addWidget(self.b_completeExplorer)
        self.lo_completeButtons.addStretch()
        self.lo_complete.addWidget(self.l_complete)
        self.lo_complete.addWidget(self.l_completeIcon)
        self.lo_complete.addWidget(self.w_completeButtons)
        self.scrollArea.widget().layout().addWidget(self.w_complete)
        self.w_complete.setHidden(True)
        self.onSettingsSourceChanged()

    @err_catcher(name=__name__)
    def enterEvent(self, event):
        QApplication.restoreOverrideCursor()

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_browse.clicked.connect(self.browse)
        self.e_name.textEdited.connect(self.nameChanged)
        self.e_path.textEdited.connect(lambda x: self.validateText(x, self.e_path))

        self.l_preview.mouseDoubleClickEvent = lambda x: self.browsePreview()
        self.l_preview.mousePressEvent = self.rclPreview
        self.l_preview.customContextMenuRequested.connect(self.rclPreview)

        self.tw_structure.mousePrEvent = self.tw_structure.mousePressEvent
        self.tw_structure.mousePressEvent = lambda x: self.mouseClickEvent(x)
        self.tw_structure.mouseClickEvent = self.tw_structure.mouseReleaseEvent
        self.tw_structure.mouseReleaseEvent = lambda x: self.mouseClickEvent(x)
        self.tw_structure.customContextMenuRequested.connect(self.rclTree)

        self.b_create.clicked.connect(self.createClicked)

        self.cb_settings.activated.connect(lambda x: self.reloadSettings())
        self.e_projectSettings.editingFinished.connect(self.reloadSettings)

        self.b_back.clicked.connect(self.backClicked)
        self.b_next.clicked.connect(self.nextClicked)
        self.cb_preset.activated.connect(lambda x: self.reloadSettings())
        self.b_settings.clicked.connect(self.customizeSettings)
        self.b_reload.clicked.connect(self.reloadSettings)
        self.b_addPreset.clicked.connect(self.createPresetDlg)
        self.b_managePresets.clicked.connect(self.managePresets)
        self.b_projectSettings.clicked.connect(self.browseProjectSettings)

    @err_catcher(name=__name__)
    def nameChanged(self, name):
        self.validateText(name, self.e_name)
        name = self.e_name.text()
        path = self.e_path.text()
        if path:
            if not name or not path.endswith(name):
                base = os.path.basename(path)
                if base == self.prevName:
                    path = os.path.dirname(path)

                path = os.path.join(path, name)
                self.e_path.setText(path)

        self.prevName = name

    @err_catcher(name=__name__)
    def mouseClickEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                index = self.tw_structure.indexAt(event.pos())
                if not index.data():
                    self.tw_structure.setCurrentIndex(
                        self.tw_structure.model().createIndex(-1, 0)
                    )
                self.tw_structure.mouseClickEvent(event)

        else:
            self.tw_structure.mousePrEvent(event)

    @err_catcher(name=__name__)
    def rclPreview(self, pos=None):
        rcmenu = QMenu(self)

        exp = QAction("Browse...", self)
        exp.triggered.connect(self.browsePreview)
        rcmenu.addAction(exp)

        copAct = QAction("Capture image", self)
        copAct.triggered.connect(self.capturePreview)
        rcmenu.addAction(copAct)
        clipAct = QAction("Paste image from clipboard", self)
        clipAct.triggered.connect(self.pastePreviewFromClipboard)
        rcmenu.addAction(clipAct)

        rcmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def capturePreview(self):
        from PrismUtils import ScreenShot

        previewImg = ScreenShot.grabScreenArea(self.core)

        if previewImg:
            previewImg = self.core.media.scalePixmap(
                previewImg,
                self.l_preview.geometry().width(),
                self.l_preview.geometry().height(),
            )
            self.previewMap = previewImg
            self.l_preview.setPixmap(self.previewMap)

    @err_catcher(name=__name__)
    def pastePreviewFromClipboard(self):
        pmap = self.core.media.getPixmapFromClipboard()
        if not pmap:
            self.core.popup("No image in clipboard.")
            return

        pmap = self.core.media.scalePixmap(
            pmap, self.l_preview.geometry().width(), self.l_preview.geometry().height()
        )
        self.previewMap = pmap
        self.l_preview.setPixmap(self.previewMap)

    @err_catcher(name=__name__)
    def browsePreview(self):
        formats = "Image File (*.jpg *.png *.exr)"

        imgPath = QFileDialog.getOpenFileName(
            self, "Select Project Image", self.core.prismRoot, formats
        )[0]

        if not imgPath:
            return

        curGeo = self.l_preview.geometry()
        if os.path.splitext(imgPath)[1] == ".exr":
            pmsmall = self.core.media.getPixmapFromExrPath(
                imgPath, width=curGeo.width(), height=curGeo.height()
            )
        else:
            pm = self.core.media.getPixmapFromPath(imgPath)
            if not pm or pm.width() == 0:
                warnStr = "Cannot read image: %s" % imgPath
                self.core.popup(warnStr)
                return

            pmsmall = self.core.media.scalePixmap(pm, curGeo.width(), curGeo.height())

        self.previewMap = pmsmall
        self.l_preview.setPixmap(self.previewMap)

    @err_catcher(name=__name__)
    def onSettingsSourceChanged(self, idx=None):
        source = self.cb_settings.currentText()
        self.l_preset.setHidden(source != "From Preset")
        self.w_preset.setHidden(source != "From Preset")
        self.l_placeholder.setHidden(True)
        self.l_projectSettings.setHidden(source != "From Project")
        self.e_projectSettings.setHidden(source != "From Project")
        self.b_projectSettings.setHidden(source != "From Project")

    @err_catcher(name=__name__)
    def reloadSettings(self):
        source = self.cb_settings.currentText()
        self.settingsApplied(None)
        if source == "From Preset":
            name = self.cb_preset.currentText()
            self.settingsApplied(self.core.projects.getDefaultProjectSettings())
            preset = self.core.projects.getPreset(name)
            if preset:
                self.core.configs.updateNestedDicts(self.projectSettings, preset["settings"])
                self.projectStructure = self.core.projects.getFolderStructureFromPath(preset["path"])

        elif source == "From Project":
            path = self.e_projectSettings.text()
            if path and os.path.isdir(path):
                configPath = self.core.configs.getProjectConfigPath(path)
                if os.path.exists(configPath):
                    settings = self.core.getConfig(configPath=configPath)
                    self.settingsApplied(self.core.projects.getDefaultProjectSettings())
                    self.core.configs.updateNestedDicts(self.projectSettings, settings)
                    self.projectStructure = self.core.projects.getFolderStructureFromPath(path, simple=True)

        if source == "Default" or not self.projectSettings:
            self.settingsApplied(self.core.projects.getDefaultProjectSettings())
            preset = self.core.projects.getPreset("Default")
            self.projectStructure = self.core.projects.getFolderStructureFromPath(preset["path"])

        self.refreshStructureTree()
        self.core.callback(
            name="onProjectCreationSettingsReloaded",
            args=[self.projectSettings]
        )
        self.settingsApplied(self.projectSettings)

    @err_catcher(name=__name__)
    def createPresetDlg(self):
        self.presetItem = PrismWidgets.CreateItem(
            core=self.core, allowChars=["_"], showType=False
        )
        self.core.parentWindow(self.presetItem, parent=self)
        self.presetItem.e_item.setFocus()
        self.presetItem.setWindowTitle("Create Preset")
        self.presetItem.l_item.setText("Preset Name:")
        self.presetItem.accepted.connect(self.createPresetFromCurrent)
        self.presetItem.show()

    @err_catcher(name=__name__)
    def createPresetFromCurrent(self):
        name = self.presetItem.e_item.text()
        settings = self.projectSettings
        structure = self.getStructureFromTree()
        text = "Creating preset. Please Wait..."
        with self.core.waitPopup(self.core, text):
            result = self.core.projects.createPresetFromSettings(
                name, settings, structure
            )

        if result:
            self.refreshPresets()
            msg = 'Created project preset "%s" successfully.' % name
            self.core.popup(msg, severity="info")

    @err_catcher(name=__name__)
    def rclTree(self, pos):
        rcmenu = QMenu(self)

        curItem = self.tw_structure.itemAt(pos)
        act_add = QAction("Add Folder...", self)
        act_add.triggered.connect(lambda: self.addFolderDlg(curItem))
        rcmenu.addAction(act_add)

        if curItem:
            act_rename = QAction("Rename...", self)
            act_rename.triggered.connect(lambda: self.renameItemDlg(curItem))
            rcmenu.addAction(act_rename)

            act_remove = QAction("Remove", self)
            act_remove.triggered.connect(lambda: self.removeItem(curItem))
            rcmenu.addAction(act_remove)

        rcmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def addFolderDlg(self, parent):
        self.folderItem = PrismWidgets.CreateItem(
            core=self.core, allowChars=["_"], showType=False
        )
        self.core.parentWindow(self.folderItem, parent=self)
        self.folderItem.e_item.setFocus()
        self.folderItem.setWindowTitle("Add Folder")
        self.folderItem.l_item.setText("Folder Name:")
        self.folderItem.accepted.connect(lambda: self.addFolderToItem(parent))
        self.folderItem.show()

    @err_catcher(name=__name__)
    def addFolderToItem(self, parent):
        name = self.folderItem.e_item.text()
        entity = {"name": name, "children": []}
        item = self.addItemToTree(entity, parent)
        if parent:
            parent.setExpanded(True)

        self.tw_structure.setCurrentItem(item)

    @err_catcher(name=__name__)
    def renameItemDlg(self, parent):
        self.rnItem = PrismWidgets.CreateItem(
            core=self.core, allowChars=["_"], showType=False
        )
        self.core.parentWindow(self.rnItem, parent=self)
        self.rnItem.e_item.setFocus()
        self.rnItem.setWindowTitle("Rename")
        self.rnItem.l_item.setText("New Name:")
        self.rnItem.buttonBox.buttons()[0].setText("Rename")
        self.rnItem.e_item.setText(parent.text(0))
        self.rnItem.e_item.selectAll()
        self.rnItem.enableOk(self.rnItem.e_item)
        self.rnItem.accepted.connect(lambda: self.renameItem(parent))
        self.rnItem.show()

    @err_catcher(name=__name__)
    def renameItem(self, item):
        name = self.rnItem.e_item.text()
        item.setText(0, name)

    @err_catcher(name=__name__)
    def removeItem(self, item):
        if item.parent():
            idx = item.parent().indexOfChild(item)
            item.parent().takeChild(idx)
        else:
            idx = self.tw_structure.indexOfTopLevelItem(item)
            self.tw_structure.takeTopLevelItem(idx)

    @err_catcher(name=__name__)
    def getStructureFromTree(self):
        rootEntity = {
            "name": "root",
            "children": [],
        }

        for topIdx in range(self.tw_structure.topLevelItemCount()):
            item = self.tw_structure.topLevelItem(topIdx)
            data = self.getStructureFromTreeItem(item)
            rootEntity["children"].append(data)

        return rootEntity

    @err_catcher(name=__name__)
    def getStructureFromTreeItem(self, item):
        entity = item.data(0, Qt.UserRole)
        entity["name"] = item.text(0)
        if "children" in entity:
            entity["children"] = []
            for idx in range(item.childCount()):
                childItem = item.child(idx)
                data = self.getStructureFromTreeItem(childItem)
                entity["children"].append(data)

        return entity

    @err_catcher(name=__name__)
    def customizeSettings(self):
        if "globals" not in self.projectSettings:
            self.projectSettings["globals"] = {}

        self.projectSettings["globals"]["project_name"] = self.getProjectName()
        self.projectSettings["globals"]["project_path"] = self.getProjectPath()
        self.dlg_settings = self.core.projects.openProjectSettings(
            projectData=self.projectSettings
        )
        self.dlg_settings.signalSaved.connect(self.settingsApplied)

    @err_catcher(name=__name__)
    def settingsApplied(self, settings):
        if settings:
            settings = copy.deepcopy(settings)

        self.projectSettings = settings or {}
        if self.enforcedSettings:
            self.projectSettings.update(copy.deepcopy(self.enforcedSettings))

    @err_catcher(name=__name__)
    def getProjectName(self):
        return self.e_name.text()

    @err_catcher(name=__name__)
    def getProjectPath(self):
        return self.e_path.text()

    @err_catcher(name=__name__)
    def managePresets(self):
        self.dlg_managePresets = ManagePresets(self)
        self.core.parentWindow(self.dlg_managePresets, parent=self)
        self.dlg_managePresets.signalPresetsChanged.connect(self.refreshPresets)
        self.dlg_managePresets.show()

    @err_catcher(name=__name__)
    def refreshPresets(self):
        self.cb_preset.blockSignals(True)
        cur = self.cb_preset.currentText()

        self.cb_preset.clear()
        presets = self.core.projects.getPresets()
        self.cb_preset.addItems([p["name"] for p in presets])
        idx = self.cb_preset.findText(cur)
        if idx != -1:
            self.cb_preset.setCurrentIndex(idx)
        else:
            self.reloadSettings()

        self.cb_preset.blockSignals(False)

    @err_catcher(name=__name__)
    def refreshStructureTree(self):
        self.tw_structure.clear()
        for entity in self.projectStructure["children"]:
            self.addItemToTree(entity)

    @err_catcher(name=__name__)
    def addItemToTree(self, entity, parent=None):
        item = QTreeWidgetItem([entity["name"]])
        item.setData(0, Qt.UserRole, entity)
        if parent:
            parent.addChild(item)
        else:
            self.tw_structure.addTopLevelItem(item)

        if "children" in entity:
            iconPath = os.path.join(
                self.core.prismRoot, "Scripts", "UserInterfacesPrism", "folder.png"
            )
            icon = self.core.media.getColoredIcon(iconPath)
            item.setIcon(0, icon)
            for child in entity["children"]:
                self.addItemToTree(child, parent=item)

        return item

    @err_catcher(name=__name__)
    def validateText(self, origText, pathUi):
        if pathUi == self.e_name:
            allowChars = ["_", " "]
        else:
            allowChars = ["/", "\\", "_", " ", ":"]

        self.core.validateLineEdit(pathUi, allowChars=allowChars)

    @err_catcher(name=__name__)
    def browse(self):
        startpath = self.getProjectPath()
        if not startpath or not os.path.exists(startpath):
            startpath = self.core.prismRoot

        path = QFileDialog.getExistingDirectory(
            self.core.messageParent, "Select project folder", startpath
        )
        if path:
            path = os.path.normpath(path)
            name = self.e_name.text()
            if not path.endswith(name):
                path = os.path.join(path, name)

            self.e_path.setText(path)
            self.validateText(path, self.e_path)

    @err_catcher(name=__name__)
    def browseProjectSettings(self):
        startpath = getattr(self.core, "projectPath", "")
        if not startpath or not os.path.exists(startpath):
            startpath = self.getProjectPath()
            if not startpath or not os.path.exists(startpath):
                startpath = self.core.prismRoot

        path = QFileDialog.getExistingDirectory(
            self.core.messageParent, "Select existing project folder", startpath
        )
        if path:
            if os.path.basename(path) == "00_Pipeline":
                path = os.path.dirname(path)

            self.e_projectSettings.setText(path)
            self.validateText(path, self.e_projectSettings)
            self.reloadSettings()

    @err_catcher(name=__name__)
    def createClicked(self):
        result = self.runSanityChecks()
        if result:
            msg = "\n".join(result)
            self.core.popup(msg)
            return

        prjName = self.getProjectName()
        prjPath = self.getProjectPath()

        if "globals" not in self.projectSettings:
            self.projectSettings["globals"] = {}

        self.projectSettings["globals"]["project_name"] = prjName
        if "project_path" in self.projectSettings["globals"]:
            del self.projectSettings["globals"]["project_path"]

        preset = self.cb_preset.currentText()
        pmap = self.l_preview.pixmap()
        structure = self.getStructureFromTree()
        result = self.core.projects.createProject(
            name=prjName,
            path=prjPath,
            settings=self.projectSettings,
            preset=preset,
            image=pmap,
            structure=structure,
        )

        if result:
            self.core.callback(
                name="onCreateProjectWindowCompleted",
                args=[self, result],
            )

            result = self.core.changeProject(result)
            if not result:
                return

            self.sw_project.setHidden(True)
            self.w_footer.setHidden(True)
            self.l_complete.setText("Project <b>%s</b> was created successfully!" % prjName)
            self.w_complete.setHidden(False)

            # self.pc = ProjectCreated(
            #     prjName, core=self.core, basepath=prjPath
            # )
            # self.pc.exec_()
            # self.close()

    @err_catcher(name=__name__)
    def backClicked(self):
        curIdx = self.sw_project.currentIndex()
        if curIdx == 0:
            return

        self.sw_project.setCurrentIndex(curIdx - 1)
        self.b_next.setVisible(True)
        self.horizontalLayout_3.itemAt(self.horizontalLayout_3.count() - 1).changeSize(
            0, 0
        )
        self.horizontalLayout_3.invalidate()
        if self.sw_project.currentIndex() == 0:
            self.b_back.setVisible(False)

    @err_catcher(name=__name__)
    def nextClicked(self):
        curIdx = self.sw_project.currentIndex()
        if curIdx == (self.sw_project.count() - 1):
            return

        self.sw_project.setCurrentIndex(curIdx + 1)
        self.b_back.setVisible(True)
        if self.sw_project.currentIndex() == (self.sw_project.count() - 1):
            self.b_next.setVisible(False)

    @err_catcher(name=__name__)
    def runSanityChecks(self):
        result = []
        prjName = self.getProjectName()
        if not prjName:
            result.append("The project name is invalid.")

        prjPath = self.getProjectPath()
        if not os.path.isabs(prjPath):
            result.append("The project path is invalid.")

        return result

    @err_catcher(name=__name__)
    def closeEvent(self, event):
        self.setParent(None)


class ManagePresets(QDialog):

    signalPresetsChanged = Signal()

    def __init__(self, parent):
        super(ManagePresets, self).__init__()
        self.core = parent.core
        self.core.parentWindow(self, parent=parent)
        self.loadLayout()
        self.refreshPresets()
        self.connectEvents()

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.setWindowTitle("Manage Project Presets")
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.lw_presets = QListWidget()
        self.w_options = QWidget()
        self.lo_options = QHBoxLayout()
        self.w_options.setLayout(self.lo_options)
        self.b_addFolder = QToolButton()
        self.b_delete = QToolButton()
        self.bb_main = QDialogButtonBox()
        self.lo_options.addStretch()
        self.lo_options.addWidget(self.b_addFolder)
        self.lo_options.addWidget(self.b_delete)
        self.lo_main.addWidget(self.lw_presets)
        self.lo_main.addWidget(self.w_options)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_addFolder.setIcon(icon)
        self.b_addFolder.setToolTip("Create new preset from existing project")

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "remove.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_delete.setIcon(icon)
        self.b_delete.setToolTip("Delete")

        self.lw_presets.setContextMenuPolicy(Qt.CustomContextMenu)

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_addFolder.clicked.connect(self.addPresetFromFolder)
        self.b_delete.clicked.connect(self.deletePreset)
        self.lw_presets.customContextMenuRequested.connect(self.presetRightClicked)

    @err_catcher(name=__name__)
    def refreshPresets(self):
        self.lw_presets.clear()
        presets = self.core.projects.getPresets()
        for preset in presets:
            item = QListWidgetItem(preset["name"])
            item.setData(Qt.UserRole, preset)
            item.setToolTip(preset["path"])
            self.lw_presets.addItem(item)

    @err_catcher(name=__name__)
    def addPresetFromFolder(self):
        path = QFileDialog.getExistingDirectory(
            self.core.messageParent, "Select project folder"
        )
        if path:
            self.newItem = PrismWidgets.CreateItem(
                core=self.core, allowChars=["_"], showType=False
            )
            self.core.parentWindow(self.newItem)
            self.newItem.e_item.setFocus()
            self.newItem.setWindowTitle("Create Preset")
            self.newItem.l_item.setText("Preset Name:")
            self.newItem.accepted.connect(lambda: self.createPreset(path))
            self.newItem.show()

    @err_catcher(name=__name__)
    def createPreset(self, path):
        name = self.newItem.e_item.text()
        self.core.projects.createPresetFromFolder(name, path)
        self.signalPresetsChanged.emit()
        self.refreshPresets()

    @err_catcher(name=__name__)
    def deletePreset(self):
        items = self.lw_presets.selectedItems()
        if not items:
            return

        item = items[0]
        name = item.text()
        if name == "Default":
            self.core.popup("Cannot delete the default project preset.")
            return

        result = self.core.popupQuestion(
            'Are you sure you want to delete the preset "%s"?' % name
        )
        if result == "Yes":
            path = item.data(Qt.UserRole)["path"]
            self.core.projects.deletePreset(path=path)
            self.signalPresetsChanged.emit()
            self.refreshPresets()

    @err_catcher(name=__name__)
    def presetRightClicked(self, pos):
        item = self.lw_presets.itemAt(pos)
        if not item:
            return

        path = item.data(Qt.UserRole)["path"]

        rcmenu = QMenu(self)
        openex = QAction("Open in Explorer", self)
        openex.triggered.connect(lambda: self.core.openFolder(path))
        rcmenu.addAction(openex)

        copAct = QAction("Copy path", self)
        copAct.triggered.connect(lambda: self.core.copyToClipboard(path))
        rcmenu.addAction(copAct)

        rcmenu.exec_(QCursor.pos())


class ProjectCreated(QDialog):
    def __init__(self, prjname, core, basepath):
        QDialog.__init__(self)
        self.core = core
        self.basepath = basepath
        self.prjname = prjname
        self.loadLayout()
        self.connectEvents()

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.setWindowTitle("Project Created")
        self.lo_main = QVBoxLayout()
        self.lo_main.setSpacing(50)
        self.setLayout(self.lo_main)
        msg = "Project <b>%s</b> was created successfully!" % self.prjname
        self.l_success = QLabel(msg)
        self.l_icon = QLabel()
        headerPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "check.png"
        )
        icon = self.core.media.getColoredIcon(headerPath, r=29, g=191, b=106, force=True)
        self.l_icon.setPixmap(icon.pixmap(60, 60))
        self.l_icon.setAlignment(Qt.AlignCenter)
        self.w_buttons = QWidget()
        self.lo_buttons = QHBoxLayout(self.w_buttons)
        self.b_browser = QPushButton("Open Project Browser")
        self.b_explorer = QPushButton("Open in Explorer")
        self.lo_main.addWidget(self.l_success)
        self.lo_main.addWidget(self.l_icon)
        self.lo_buttons.addStretch()
        self.lo_buttons.addWidget(self.b_browser)
        self.lo_buttons.addWidget(self.b_explorer)
        self.lo_buttons.addStretch()
        self.lo_main.addWidget(self.w_buttons)
        self.core.parentWindow(self)
        self.setFocus()

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_browser.clicked.connect(self.core.projectBrowser)
        self.b_browser.clicked.connect(self.accept)
        self.b_explorer.clicked.connect(lambda: self.core.openFolder(self.core.projectPath))
        self.b_explorer.clicked.connect(self.accept)


class SetProject(QDialog):
    def __init__(self, core, openUi=""):
        QDialog.__init__(self)
        self.core = core
        self.core.parentWindow(self)
        self.setWindowTitle("Set Project")

        self.openUi = openUi

        self.projectsUi = SetProjectClass(self.core, self, openUi)
        self.loadLayout()
        self.setFocus()

    @err_catcher(name=__name__)
    def loadLayout(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.projectsUi)

        self.setLayout(grid)

        self.w_header = DragWidget(self)
        self.w_header.setAttribute(Qt.WA_StyledBackground, True)
        self.w_header.setStyleSheet("DragWidget{ background-color: rgba(0, 0, 0, 30) }")
        self.w_header.setGeometry(0, 0, self.width(), 40)
        self.b_close = QToolButton(self)
        self.b_close.move((self.width() - self.b_close.geometry().width() - 10), 10)
        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(path, force=True)
        self.b_close.setIcon(icon)
        self.b_close.clicked.connect(self.close)
        self.b_close.setIconSize(QSize(20, 20))
        self.b_close.setToolTip("Close")
        self.b_close.setMaximumWidth(20)
        self.b_close.setMaximumHeight(20)
        self.b_close.setStyleSheet(
            "QToolButton{padding: 0; margin: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 0px; background-color: rgba(255, 255, 255, 30)}"
        )

        #    self.resize(self.projectsUi.width(), self.projectsUi.height())
        if self.projectsUi.getProjects():
            self.resize(800, 900)
        else:
            self.resize(
                self.projectsUi.l_header.pixmap().width(),
                self.projectsUi.l_header.pixmap().height(),
            )

        self.setWindowFlags(
            self.windowFlags() ^ Qt.FramelessWindowHint
        )

    @err_catcher(name=__name__)
    def resizeEvent(self, event):
        self.b_close.move((self.width() - self.b_close.geometry().width() - 10), 10)
        self.w_header.setGeometry(0, 0, self.width(), 40)


class SetProjectClass(QDialog):

    signalShowing = Signal()

    def __init__(self, core, pdialog, openUi="", refresh=True):
        QDialog.__init__(self)
        self.core = core
        self.pdialog = pdialog
        self.openUi = openUi
        self.allowDeselect = True

        self.loadLayout()
        self.connectEvents()
        if refresh:
            self.refreshUi()

        self.core.callback(name="onSetProjectStartup", args=[self])

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.chb_startup.stateChanged.connect(self.startupChanged)

    @err_catcher(name=__name__)
    def enterEvent(self, event):
        try:
            QApplication.restoreOverrideCursor()
        except:
            pass

    @err_catcher(name=__name__)
    def preCreate(self):
        self.core.projects.createProjectDialog()
        self.pdialog.close()
        if getattr(self.core, "pb", None) and self.core.pb.isVisible():
            self.core.pb.close()

    @err_catcher(name=__name__)
    def openProject(self, widget):
        path = widget.data["configPath"]
        if path == self.core.prismIni:
            msg = "This project is already active."
            self.core.popup(msg, parent=self)
            return

        self.core.changeProject(path, self.openUi)

    @err_catcher(name=__name__)
    def getProjectWidgetClass(self):
        return self.core.projects.ProjectWidget

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_header = QLabel()
        headerPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "prism_title.png"
        )
        pmap = self.core.media.getPixmapFromPath(headerPath)
        pmap = self.core.media.scalePixmap(pmap, 800, 500)
        self.l_header.setPixmap(pmap)
        self.l_header.setAlignment(Qt.AlignTop)

        self.w_newProject = QWidget()
        self.w_newProjectV = QWidget()
        self.lo_newProjectV = QVBoxLayout()
        self.w_newProjectV.setLayout(self.lo_newProjectV)
        self.lo_newProject = QHBoxLayout()
        self.lo_newProject.setSpacing(20)
        self.w_newProject.setLayout(self.lo_newProject)
        self.w_projects = QWidget()
        self.lo_projects = QGridLayout()
        self.lo_projects.setSpacing(30)
        self.w_projects.setLayout(self.lo_projects)
        self.w_bottomWidgets = QWidget()
        self.lo_bottomWidgets = QHBoxLayout(self.w_bottomWidgets)
        self.chb_startup = QCheckBox("Open on startup")
        ssheet = self.chb_startup.styleSheet() + ";QCheckBox::indicator{border-width: 1px}"
        self.chb_startup.setStyleSheet(ssheet)
        self.b_settings = QToolButton()
        self.b_settings.setToolTip("Open Prism Settings...")
        self.b_settings.setStyleSheet(
            "QToolButton{padding: 0; margin: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 0px; background-color: rgba(255, 255, 255, 30)}"
        )
        self.b_settings.clicked.connect(self.core.prismSettings)
        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "configure.png"
        )
        icon = self.core.media.getColoredIcon(path, force=True)
        self.b_settings.setIcon(icon)
        self.lo_bottomWidgets.addWidget(self.chb_startup)
        self.lo_bottomWidgets.addStretch()
        self.lo_bottomWidgets.addWidget(self.b_settings)
        self.lo_main = QVBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)

        self.w_scrollParent = QWidget()
        self.lo_scrollParent = QHBoxLayout()
        self.sa_projects = QScrollArea()
        self.sa_projects.setWidgetResizable(True)
        self.sa_projects.setWidget(self.w_projects)
        self.w_scrollParent.setLayout(self.lo_scrollParent)
        self.lo_scrollParent.addWidget(self.sa_projects)
        self.lo_main.addWidget(self.l_header)
        self.lo_main.addWidget(self.w_scrollParent)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        data = {"name": "Create New Project...", "icon": path}
        self.w_new = self.getProjectWidgetClass()(self, data)
        self.w_new.setMaximumHeight(100)
        self.w_new.setMinimumWidth(200)
        self.w_new.signalReleased.connect(lambda x: self.preCreate())
        self.w_new.signalReleased.connect(lambda x: x.deselect())

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "browse.png"
        )
        data = {"name": "Open Existing Project...", "icon": path}
        self.w_open = self.getProjectWidgetClass()(self, data)
        self.w_open.setMaximumHeight(100)
        self.w_open.setMinimumWidth(200)
        self.w_open.signalReleased.connect(lambda x: self.core.projects.openProject(parent=self.pdialog))
        self.w_open.signalReleased.connect(lambda x: x.deselect())

        self.lo_newProject.addStretch()
        self.lo_newProject.addWidget(self.w_new)
        self.lo_newProject.addWidget(self.w_open)
        self.lo_newProject.addStretch()
        self.lo_newProjectV.addStretch()
        self.lo_newProjectV.addWidget(self.w_newProject)
        self.lo_newProjectV.addWidget(self.w_bottomWidgets)
        self.w_newProjectV.setParent(self)
        self.w_newProjectV.setGeometry(
            0, 0, self.l_header.width(), self.l_header.height()
        )

        ssu = self.core.getConfig("globals", "showonstartup")
        if ssu is None:
            ssu = True

        if self.core.appPlugin.pluginName == "Standalone":
            self.chb_startup.setVisible(False)

        self.chb_startup.setChecked(ssu)

    @err_catcher(name=__name__)
    def resizeEvent(self, event):
        self.w_newProjectV.setGeometry(
            0, 0, self.l_header.width(), self.l_header.height()
        )

    @err_catcher(name=__name__)
    def refreshUi(self):
        self._projects = None
        self.projectWidgets = []
        for idx in reversed(range(self.lo_projects.count())):
            item = self.lo_projects.takeAt(idx)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        projects = self.getProjects()
        for project in projects:
            w_prj = self.getProjectWidgetClass()(self, project.copy(), minHeight=1)
            w_prj.signalDoubleClicked.connect(self.openProject)
            w_prj.signalRemoved.connect(self.refreshUi)
            w_prj.signalSelect.connect(self.itemSelected)
            self.projectWidgets.append(w_prj)
            self.lo_projects.addWidget(
                w_prj,
                int(self.lo_projects.count() / 3),
                1 + (self.lo_projects.count() % 3) + (self.lo_projects.count() % 3),
            )

        sp_projectsR = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lo_projects.setColumnStretch(0, 100)
        sp_projectsL = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        sp_projectsR2 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        sp_projectsL2 = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        sp_projectsB = QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.lo_projects.addItem(sp_projectsR, 0, 0)
        self.lo_projects.setColumnStretch(0, 100)
        self.lo_projects.addItem(sp_projectsL, 0, 2)
        self.lo_projects.setColumnStretch(2, 100)
        if len(projects) > 1:
            self.lo_projects.addItem(sp_projectsR2, 0, 4)
            self.lo_projects.setColumnStretch(4, 100)
            if len(projects) > 2:
                self.lo_projects.addItem(sp_projectsL2, 0, 6)
                self.lo_projects.setColumnStretch(6, 100)

        self.lo_projects.addItem(sp_projectsB, self.lo_projects.rowCount(), 0)
        self.w_scrollParent.setHidden(not bool(projects))
        for widget in self.projectWidgets:
            if widget.data.get("configPath", None) == self.core.prismIni:
                widget.select()

    @err_catcher(name=__name__)
    def itemSelected(self, item, event=None):
        if not self.allowDeselect:
            return

        mods = QApplication.keyboardModifiers()
        if item.isSelected():
            if mods == Qt.ControlModifier and (not event or event.button() == Qt.LeftButton):
                item.deselect()
        else:
            if mods != Qt.ControlModifier:
                self.deselectItems(ignore=[item])

    @err_catcher(name=__name__)
    def deselectItems(self, ignore=None):
        for item in self.projectWidgets:
            if ignore and item in ignore:
                continue

            item.deselect()

    @err_catcher(name=__name__)
    def startupChanged(self, state):
        if state == 0:
            self.core.setConfig("globals", "showonstartup", False)
        elif state == 2:
            self.core.setConfig("globals", "showonstartup", True)

    @err_catcher(name=__name__)
    def getProjects(self):
        if not hasattr(self, "_projects") or self._projects is None:
            self._projects = self.core.projects.getAvailableProjects(includeCurrent=True)

        return self._projects

    @err_catcher(name=__name__)
    def getSelectedItems(self):
        items = []
        for item in self.projectWidgets:
            if item.isSelected():
                items.append(item)

        return items

    @err_catcher(name=__name__)
    def showEvent(self, event):
        self.signalShowing.emit()


class DragWidget(QWidget):
    @err_catcher(name=__name__)
    def mousePressEvent(self, event):
        self.startPos = event.pos()

    @err_catcher(name=__name__)
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            diff = event.pos() - self.startPos
            newpos = self.parent().pos() + diff
            self.parent().move(newpos)


class CreateAssetDlg(PrismWidgets.CreateItem):
    def __init__(self, core, parent=None, startText=None):
        startText = startText or ""
        super(CreateAssetDlg, self).__init__(startText=startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])
        self.parentDlg = parent
        self.core = core
        self.thumbXres = 250
        self.thumbYres = 141
        self.imgPath = ""
        self.pmap = None
        self.setupUi_()

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create Asset...")
        self.core.parentWindow(self, parent=self.parentDlg)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[0].setIcon(icon)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[2].setIcon(icon)

        self.w_item.setContentsMargins(0, 0, 0, 0)
        self.e_item.setFocus()
        self.e_item.setToolTip("Asset name or comma separated list of asset names.\nParent nFolders can be included using slashes.")
        self.l_item.setText("Asset(s):")
        # self.l_assetIcon = QLabel()
        # self.w_item.layout().insertWidget(0, self.l_assetIcon)
        # iconPath = os.path.join(
        #     self.core.prismRoot, "Scripts", "UserInterfacesPrism", "asset.png"
        # )
        # icon = self.core.media.getColoredIcon(iconPath)
        # self.l_assetIcon.setPixmap(icon.pixmap(15, 15))

        self.layout().setContentsMargins(20, 20, 20, 20)

        self.w_thumbnail = QWidget()
        self.lo_thumbnail = QHBoxLayout(self.w_thumbnail)
        self.lo_thumbnail.setContentsMargins(0, 0, 0, 0)
        self.l_thumbnailStr = QLabel("Thumbnail:")
        self.l_thumbnail = QLabel()
        self.lo_thumbnail.addWidget(self.l_thumbnailStr)
        self.lo_thumbnail.addWidget(self.l_thumbnail)
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_thumbnail)

        self.w_taskPreset = QWidget()
        self.lo_taskPreset = QHBoxLayout(self.w_taskPreset)
        self.lo_taskPreset.setContentsMargins(0, 0, 0, 0)
        self.l_taskPreset = QLabel("Task Preset:")
        self.chb_taskPreset = QCheckBox()
        self.cb_taskPreset = QComboBox()
        self.cb_taskPreset.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.lo_taskPreset.addWidget(self.l_taskPreset)
        self.lo_taskPreset.addStretch()
        self.lo_taskPreset.addWidget(self.chb_taskPreset)
        self.lo_taskPreset.addWidget(self.cb_taskPreset)
        self.cb_taskPreset.setEnabled(self.chb_taskPreset.isChecked())
        self.chb_taskPreset.toggled.connect(self.cb_taskPreset.setEnabled)
        presets = self.core.projects.getAssetTaskPresets()
        if presets:
            for preset in presets:
                self.cb_taskPreset.addItem(preset.get("name", ""), preset)

            self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.w_taskPreset)

        self.l_info = QLabel("Description:")
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.l_info)
        self.te_text = QTextEdit()
        self.layout().insertWidget(self.layout().indexOf(self.buttonBox)-2, self.te_text)

        import MetaDataWidget
        self.w_meta = MetaDataWidget.MetaDataWidget(self.core)
        self.layout().insertWidget(
            self.layout().indexOf(self.buttonBox)-2, self.w_meta
        )
        # self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.layout().insertItem(
        #     self.layout().indexOf(self.buttonBox), self.spacer
        # )

        imgFile = os.path.join(
            self.core.projects.getFallbackFolder(), "noFileSmall.jpg"
        )
        pmap = self.core.media.getPixmapFromPath(imgFile)
        if pmap:
            self.l_thumbnail.setMinimumSize(pmap.width(), pmap.height())
            self.l_thumbnail.setPixmap(pmap)

        self.l_thumbnail.setContextMenuPolicy(Qt.CustomContextMenu)

        self.l_thumbnail.mouseReleaseEvent = self.previewMouseReleaseEvent
        self.l_thumbnail.customContextMenuRequested.connect(self.rclThumbnail)
        self.resize(450, 550)

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(450, 450)

    @err_catcher(name=__name__)
    def previewMouseReleaseEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.rclThumbnail()

    @err_catcher(name=__name__)
    def rclThumbnail(self, pos=None):
        rcmenu = QMenu(self)

        copAct = QAction("Capture thumbnail", self)
        copAct.triggered.connect(self.capturePreview)
        rcmenu.addAction(copAct)

        copAct = QAction("Browse thumbnail...", self)
        copAct.triggered.connect(self.browsePreview)
        rcmenu.addAction(copAct)

        clipAct = QAction("Paste thumbnail from clipboard", self)
        clipAct.triggered.connect(self.pastePreviewFromClipboard)
        rcmenu.addAction(clipAct)

        rcmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def capturePreview(self):
        from PrismUtils import ScreenShot

        previewImg = ScreenShot.grabScreenArea(self.core)

        if previewImg:
            previewImg = self.core.media.scalePixmap(
                previewImg,
                self.thumbXres,
                self.thumbYres,
            )
            self.setPixmap(previewImg)

    @err_catcher(name=__name__)
    def pastePreviewFromClipboard(self):
        pmap = self.core.media.getPixmapFromClipboard()
        if not pmap:
            self.core.popup("No image in clipboard.", parent=self)
            return

        pmap = self.core.media.scalePixmap(
            pmap,
            self.thumbXres,
            self.thumbYres,
        )
        self.setPixmap(pmap)

    @err_catcher(name=__name__)
    def browsePreview(self):
        formats = "Image File (*.jpg *.png *.exr)"

        imgPath = QFileDialog.getOpenFileName(
            self, "Select thumbnail-image", self.imgPath, formats
        )[0]

        if not imgPath:
            return

        if os.path.splitext(imgPath)[1] == ".exr":
            pmsmall = self.core.media.getPixmapFromExrPath(
                imgPath,
                width=self.thumbXres,
                height=self.thumbYres,
            )
        else:
            pm = self.core.media.getPixmapFromPath(imgPath)
            if pm.width() == 0:
                warnStr = "Cannot read image: %s" % imgPath
                self.core.popup(warnStr, parent=self)
                return

            pmsmall = self.core.media.scalePixmap(
                pm,
                self.thumbXres,
                self.thumbYres,
            )

        self.setPixmap(pmsmall)

    @err_catcher(name=__name__)
    def setPixmap(self, pmsmall):
        self.pmap = pmsmall
        self.l_thumbnail.setMinimumSize(self.pmap.width(), self.pmap.height())
        self.l_thumbnail.setPixmap(self.pmap)

    @err_catcher(name=__name__)
    def getDescription(self):
        return self.te_text.toPlainText()
    
    @err_catcher(name=__name__)
    def getThumbnail(self):
        return self.pmap


class CreateFolderDlg(PrismWidgets.CreateItem):
    def __init__(self, core, parent=None, startText=None):
        startText = startText or ""
        super(CreateFolderDlg, self).__init__(startText=startText.lstrip("/"), core=core, mode="assetHierarchy", allowChars=["/"])
        self.parentDlg = parent
        self.core = core
        self.setupUi_()

    @err_catcher(name=__name__)
    def setupUi_(self):
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "create.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[0].setIcon(icon)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.buttonBox.buttons()[2].setIcon(icon)

        self.core.parentWindow(self, parent=self.parentDlg)
        self.e_item.setFocus()
        self.e_item.setToolTip("Folder name or comma separated list of folder names.\nParent folders can be included using slashes.")
        self.setWindowTitle("Create Folder...")
        self.l_item.setText("Folder(s):")


class CreateProductDlg(QDialog):
    def __init__(self, origin, entity=None):
        super(CreateProductDlg, self).__init__()
        self.parentDlg = origin
        self.core = self.parentDlg.core
        self.core.parentWindow(self, parent=self.parentDlg)
        self.entity = entity
        self.setupUi_()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(300, 150)

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create Product")
        self.lo_main = QVBoxLayout(self)

        self.w_settings = QWidget()
        self.lo_settings = QGridLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 9, 0, 9)

        row = 0
        if self.core.mediaProducts.getLinkedToTasks():
            self.l_department = QLabel("Department:")
            self.e_department = QLineEdit()
            self.e_department.textEdited.connect(lambda x: self.enableOk())
            self.b_department = QPushButton("▼")
            self.b_department.setMaximumSize(QSize(25, 16777215))
            self.b_department.clicked.connect(self.onDepartmentClicked)
            self.lo_settings.addWidget(self.l_department, row, 0)
            self.lo_settings.addWidget(self.e_department, row, 1)
            self.lo_settings.addWidget(self.b_department, row, 2)
            row += 1

            self.l_task = QLabel("Task:")
            self.e_task = QLineEdit()
            self.e_task.textEdited.connect(lambda x: self.enableOk())
            self.b_task = QPushButton("▼")
            self.b_task.setMaximumSize(QSize(25, 16777215))
            self.b_task.clicked.connect(self.onTaskClicked)
            self.lo_settings.addWidget(self.l_task, row, 0)
            self.lo_settings.addWidget(self.e_task, row, 1)
            self.lo_settings.addWidget(self.b_task, row, 2)
            row += 1

            fileName = self.core.getCurrentFileName()
            context = self.core.getScenefileData(fileName)

            dep = context.get("department") or ""
            if self.entity.get("type") == "asset":
                departments = self.core.projects.getAssetDepartments()
            elif self.entity.get("type") == "shot":
                departments = self.core.projects.getShotDepartments()
            else:
                departments = []

            if not dep and departments:
                dep = departments[0]["abbreviation"]

            task = context.get("task") or ""
            if not task and dep:
                tasks = self.core.entities.getCategories(self.entity, dep)
                dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), dep)
                for dftTask in dftTasks:
                    if dftTask not in tasks:
                        tasks.append(dftTask)

                if tasks:
                    task = sorted(tasks, key=lambda x: x.lower())[0]

            self.e_department.setText(dep)
            self.e_task.setText(task)

        self.l_product = QLabel("Product:")
        self.e_product = QLineEdit()
        self.e_product.textEdited.connect(lambda x: self.enableOk())
        self.lo_settings.addWidget(self.l_product, row, 0)
        self.lo_settings.addWidget(self.e_product, row, 1)
        row += 1

        self.l_location = QLabel("Location:")
        self.cb_location = QComboBox()
        locs = self.core.paths.getExportProductBasePaths()
        for loc in list(locs.keys()):
            self.cb_location.addItem(loc)

        self.lo_settings.addWidget(self.l_location, row, 0)
        self.lo_settings.addWidget(self.cb_location, row, 1)
        if len(locs) < 2:
            self.l_location.setHidden(True)
            self.cb_location.setHidden(True)

        row += 1

        self.bb_main = QDialogButtonBox()
        self.b_create = self.bb_main.addButton("Create", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.b_create.setEnabled(False)
        self.bb_main.accepted.connect(self.createClicked)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addWidget(self.w_settings)
        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def onDepartmentClicked(self):
        tmenu = QMenu(self)

        if self.entity.get("type") == "asset":
            departments = self.core.projects.getAssetDepartments()
        elif self.entity.get("type") == "shot":
            departments = self.core.projects.getShotDepartments()
        else:
            departments = []

        for dep in departments:
            tAct = QAction(dep["abbreviation"], self)
            tAct.triggered.connect(lambda x=None, d=dep["abbreviation"]: self.e_department.setText(d))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onTaskClicked(self):
        tmenu = QMenu(self)

        tasks = self.core.entities.getCategories(self.entity, self.e_department.text())
        dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), self.e_department.text())
        for dftTask in dftTasks:
            if dftTask not in tasks:
                tasks.append(dftTask)

        for task in sorted(tasks, key=lambda x: x.lower()):
            tAct = QAction(task, self)
            tAct.triggered.connect(lambda x=None, t=task: self.e_task.setText(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def createClicked(self):
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.core.validateLineEdit(self.e_department)
            if not depText:
                self.core.popup("Invalid department.")
                return

            taskText = self.core.validateLineEdit(self.e_task)
            if not taskText:
                self.core.popup("Invalid task.")
                return

        prdText = self.core.validateLineEdit(self.e_product)
        if not prdText:
            self.core.popup("Invalid product.")
            return

        self.accept()

    @err_catcher(name=__name__)
    def enableOk(self):
        prdText = self.core.validateLineEdit(self.e_product)
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.core.validateLineEdit(self.e_department)
            taskText = self.core.validateLineEdit(self.e_task)
            valid = bool(prdText and depText and taskText)
        else:
            valid = bool(prdText)

        self.b_create.setEnabled(valid)


class CreateProductVersionDlg(QDialog):
    def __init__(self, origin, entity=None):
        super(CreateProductVersionDlg, self).__init__()
        self.parentDlg = origin
        self.core = self.parentDlg.core
        self.core.parentWindow(self, parent=self.parentDlg)
        self.entity = entity
        self.setupUi_()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(500, 150)

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create Version")
        self.lo_main = QVBoxLayout(self)

        self.w_settings = QWidget()
        self.lo_settings = QGridLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 9, 0, 9)

        row = 0
        self.l_version = QLabel("Version:")
        self.sp_version = VersionSpinBox()
        self.sp_version.core = self.core
        self.sp_version.setRange(self.core.lowestVersion, 99999)
        self.lo_settings.addWidget(self.l_version, row, 0)
        self.lo_settings.addWidget(self.sp_version, row, 1)
        row += 1

        self.l_location = QLabel("Location:")
        self.cb_location = QComboBox()
        locs = self.core.paths.getExportProductBasePaths()
        for loc in list(locs.keys()):
            self.cb_location.addItem(loc)

        self.lo_settings.addWidget(self.l_location, row, 0)
        self.lo_settings.addWidget(self.cb_location, row, 1)
        if len(locs) < 2:
            self.l_location.setHidden(True)
            self.cb_location.setHidden(True)

        row += 1

        self.w_filePath = QWidget()
        self.w_filePath.setObjectName("fileWidget")
        self.l_filePathLabel = QLabel("File Path:")
        self.l_filePath = QLabel("< Click or Drag & Drop files >")
        self.l_filePath.setAlignment(Qt.AlignCenter)
        self.l_filePath.setCursor(Qt.PointingHandCursor)
        self.l_filePath.mouseReleaseEvent = self.fileMouseClickEvent
        self.lo_filePath = QHBoxLayout(self.w_filePath)
        self.lo_filePath.setContentsMargins(0, 20, 0, 20)
        self.lo_filePath.addWidget(self.l_filePath)
        self.lo_settings.addWidget(self.l_filePathLabel, row, 0)
        self.lo_settings.addWidget(self.w_filePath, row, 1)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.w_filePath.setSizePolicy(sizePolicy)
        self.w_filePath.setAcceptDrops(True)
        self.w_filePath.dragEnterEvent = self.fileDragEnterEvent
        self.w_filePath.dragMoveEvent = self.fileDragMoveEvent
        self.w_filePath.dragLeaveEvent = self.fileDragLeaveEvent
        self.w_filePath.dropEvent = self.fileDropEvent

        row += 1

        self.bb_main = QDialogButtonBox()
        self.b_create = self.bb_main.addButton("Create", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.bb_main.accepted.connect(self.createClicked)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addWidget(self.w_settings)
        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def fileMouseClickEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            tmenu = QMenu(self)

            tAct = QAction("Select File...", self)
            tAct.triggered.connect(self.browseFile)
            tmenu.addAction(tAct)

            tAct = QAction("Select Folder...", self)
            tAct.triggered.connect(self.browseFolder)
            tmenu.addAction(tAct)

            tAct = QAction("Copy", self)
            tAct.triggered.connect(lambda: self.core.copyToClipboard(self.l_filePath.text()))
            tmenu.addAction(tAct)

            tAct = QAction("Open in Explorer", self)
            tAct.triggered.connect(self.openFolder)
            tmenu.addAction(tAct)

            tAct = QAction("Clear", self)
            tAct.triggered.connect(self.clearFiles)
            tmenu.addAction(tAct)

            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def fileDragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def fileDragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
            self.w_filePath.setStyleSheet(
                "QWidget#fileWidget { border-style: dashed; border-color: rgb(100, 200, 100);  border-width: 2px; }"
            )
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def fileDragLeaveEvent(self, e):
        self.w_filePath.setStyleSheet("")

    @err_catcher(name=__name__)
    def fileDropEvent(self, e):
        if e.mimeData().hasUrls():
            self.w_filePath.setStyleSheet("")
            e.setDropAction(Qt.LinkAction)
            e.accept()

            fname = [
                os.path.normpath(str(url.toLocalFile())) for url in e.mimeData().urls()
            ]
            self.l_filePath.setText("\n".join(fname))
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def browseFolder(self):
        startpath = self.l_filePath.text() or self.core.projectPath
        selectedPath = QFileDialog.getExistingDirectory(
            self, "Select folder", startpath
        )

        if selectedPath:
            self.l_filePath.setText(selectedPath.replace("\\", "/"))

    @err_catcher(name=__name__)
    def browseFile(self):
        startpath = self.l_filePath.text() or self.core.projectPath
        selectedFile = QFileDialog.getOpenFileName(
            self, "Select file", startpath
        )[0]

        if selectedFile:
            self.l_filePath.setText(selectedFile.replace("\\", "/"))

    @err_catcher(name=__name__)
    def openFolder(self):
        path = self.l_filePath.text()
        self.core.openFolder(path)

    @err_catcher(name=__name__)
    def clearFiles(self):
        self.l_filePath.setText("< Click or Drag & Drop files >")

    @err_catcher(name=__name__)
    def createClicked(self):
        self.accept()


class CreateIdentifierDlg(QDialog):
    def __init__(self, origin, entity=None):
        super(CreateIdentifierDlg, self).__init__()
        self.parentDlg = origin
        self.core = self.parentDlg.core
        self.core.parentWindow(self, parent=self.parentDlg)
        self.entity = entity
        self.setupUi_()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(300, 150)

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create Identifier")
        self.lo_main = QVBoxLayout(self)

        self.w_settings = QWidget()
        self.lo_settings = QGridLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 9, 0, 9)

        row = 0
        if self.core.mediaProducts.getLinkedToTasks():
            self.l_department = QLabel("Department:")
            self.e_department = QLineEdit()
            self.e_department.textEdited.connect(lambda x: self.enableOk())
            self.b_department = QPushButton("▼")
            self.b_department.setMaximumSize(QSize(25, 16777215))
            self.b_department.clicked.connect(self.onDepartmentClicked)
            self.lo_settings.addWidget(self.l_department, row, 0)
            self.lo_settings.addWidget(self.e_department, row, 1)
            self.lo_settings.addWidget(self.b_department, row, 2)
            row += 1

            self.l_task = QLabel("Task:")
            self.e_task = QLineEdit()
            self.e_task.textEdited.connect(lambda x: self.enableOk())
            self.b_task = QPushButton("▼")
            self.b_task.setMaximumSize(QSize(25, 16777215))
            self.b_task.clicked.connect(self.onTaskClicked)
            self.lo_settings.addWidget(self.l_task, row, 0)
            self.lo_settings.addWidget(self.e_task, row, 1)
            self.lo_settings.addWidget(self.b_task, row, 2)
            row += 1

            fileName = self.core.getCurrentFileName()
            context = self.core.getScenefileData(fileName)

            dep = context.get("department") or ""
            if self.entity.get("type") == "asset":
                departments = self.core.projects.getAssetDepartments()
            elif self.entity.get("type") == "shot":
                departments = self.core.projects.getShotDepartments()
            else:
                departments = []

            if not dep and departments:
                dep = departments[0]["abbreviation"]

            task = context.get("task") or ""
            if not task and dep:
                tasks = self.core.entities.getCategories(self.entity, dep)
                dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), dep)
                for dftTask in dftTasks:
                    if dftTask not in tasks:
                        tasks.append(dftTask)

                if tasks:
                    task = sorted(tasks, key=lambda x: x.lower())[0]

            self.e_department.setText(dep)
            self.e_task.setText(task)

        self.l_identifier = QLabel("Identifier:")
        self.e_identifier = QLineEdit()
        self.e_identifier.textEdited.connect(lambda x: self.enableOk())
        self.lo_settings.addWidget(self.l_identifier, row, 0)
        self.lo_settings.addWidget(self.e_identifier, row, 1)
        row += 1

        self.l_mediaType = QLabel("Type:")
        self.cb_mediaType = QComboBox()
        self.cb_mediaType.addItems(["3D", "2D", "Playblast", "External"])
        self.lo_settings.addWidget(self.l_mediaType, row, 0)
        self.lo_settings.addWidget(self.cb_mediaType, row, 1)
        row += 1

        self.l_location = QLabel("Location:")
        self.cb_location = QComboBox()
        locs = self.core.paths.getRenderProductBasePaths()
        for loc in list(locs.keys()):
            self.cb_location.addItem(loc)

        self.lo_settings.addWidget(self.l_location, row, 0)
        self.lo_settings.addWidget(self.cb_location, row, 1)
        if len(locs) < 2:
            self.l_location.setHidden(True)
            self.cb_location.setHidden(True)

        row += 1

        self.bb_main = QDialogButtonBox()
        self.b_create = self.bb_main.addButton("Create", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.b_create.setEnabled(False)
        self.bb_main.accepted.connect(self.createClicked)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addWidget(self.w_settings)
        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def onDepartmentClicked(self):
        tmenu = QMenu(self)

        if self.entity.get("type") == "asset":
            departments = self.core.projects.getAssetDepartments()
        elif self.entity.get("type") == "shot":
            departments = self.core.projects.getShotDepartments()
        else:
            departments = []

        for dep in departments:
            tAct = QAction(dep["abbreviation"], self)
            tAct.triggered.connect(lambda x=None, d=dep["abbreviation"]: self.e_department.setText(d))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onTaskClicked(self):
        tmenu = QMenu(self)

        tasks = self.core.entities.getCategories(self.entity, self.e_department.text())
        dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), self.e_department.text()) or []
        for dftTask in dftTasks:
            if dftTask not in tasks:
                tasks.append(dftTask)

        for task in sorted(tasks, key=lambda x: x.lower()):
            tAct = QAction(task, self)
            tAct.triggered.connect(lambda x=None, t=task: self.e_task.setText(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def createClicked(self):
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.core.validateLineEdit(self.e_department)
            if not depText:
                self.core.popup("Invalid department.")
                return

            taskText = self.core.validateLineEdit(self.e_task)
            if not taskText:
                self.core.popup("Invalid task.")
                return

        idfText = self.core.validateLineEdit(self.e_identifier)
        if not idfText:
            self.core.popup("Invalid identifier.")
            return

        self.accept()

    @err_catcher(name=__name__)
    def enableOk(self):
        idfText = self.core.validateLineEdit(self.e_identifier)
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.core.validateLineEdit(self.e_department)
            taskText = self.core.validateLineEdit(self.e_task)
            valid = bool(idfText and depText and taskText)
        else:
            valid = bool(idfText)

        self.b_create.setEnabled(valid)


class CreateMediaVersionDlg(QDialog):
    def __init__(self, origin, entity=None):
        super(CreateMediaVersionDlg, self).__init__()
        self.parentDlg = origin
        self.core = self.parentDlg.core
        self.core.parentWindow(self, parent=self.parentDlg)
        self.entity = entity
        self.setupUi_()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(300, 150)

    @err_catcher(name=__name__)
    def setupUi_(self):
        self.setWindowTitle("Create Version")
        self.lo_main = QVBoxLayout(self)

        self.w_settings = QWidget()
        self.lo_settings = QGridLayout(self.w_settings)
        self.lo_settings.setContentsMargins(0, 9, 0, 9)

        row = 0
        self.l_version = QLabel("Version:")
        self.sp_version = VersionSpinBox()
        self.sp_version.core = self.core
        self.sp_version.setRange(self.core.lowestVersion, 99999)
        self.lo_settings.addWidget(self.l_version, row, 0)
        self.lo_settings.addWidget(self.sp_version, row, 1)
        row += 1

        self.l_location = QLabel("Location:")
        self.cb_location = QComboBox()
        locs = self.core.paths.getRenderProductBasePaths()
        for loc in list(locs.keys()):
            self.cb_location.addItem(loc)

        self.lo_settings.addWidget(self.l_location, row, 0)
        self.lo_settings.addWidget(self.cb_location, row, 1)
        if len(locs) < 2:
            self.l_location.setHidden(True)
            self.cb_location.setHidden(True)

        row += 1

        self.bb_main = QDialogButtonBox()
        self.b_create = self.bb_main.addButton("Create", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.bb_main.accepted.connect(self.createClicked)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addWidget(self.w_settings)
        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def createClicked(self):
        self.accept()


class IngestMediaDlg(QDialog):
    def __init__(self, core, startText="", entity=None, parent=None):
        QDialog.__init__(self)
        self.core = core
        self.entity = entity
        self.core.parentWindow(self, parent=parent)
        self.setupUi()
        self.onMediaTypeChanged()
        self.setEntity(entity)
        if startText:
            self.setMediaPaths(startText)
            if len(self.l_mediaPath.text().split("\n")) > 10:
                self.resize(800, 800)

        self.sp_version.setValue(1)
        self.b_create.setEnabled(False)
        self.connectEvents()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(800, 200)

    @err_catcher(name=__name__)
    def setupUi(self):
        self.setWindowTitle("Ingest Media")

        self.lo_main = QVBoxLayout(self)
        self.w_settings = QWidget()
        self.lo_settings = QGridLayout(self.w_settings)

        row = 0

        self.l_entity = QLabel("Entity:")
        self.w_entity = QWidget()
        self.lo_entity = QHBoxLayout(self.w_entity)
        self.w_entity.setCursor(Qt.PointingHandCursor)
        self.w_entity.mouseReleaseEvent = self.entityMouseClickEvent
        self.l_entityPreview = QLabel()
        self.l_entityName = QLabel()
        self.lo_entity.addWidget(self.l_entityPreview)
        self.lo_entity.addWidget(self.l_entityName)
        self.lo_settings.addWidget(self.l_entity, row, 0)
        self.lo_settings.addWidget(self.w_entity, row, 1)
        row += 1

        self.l_location = QLabel("Location:")
        self.cb_location = QComboBox()
        locs = self.core.paths.getRenderProductBasePaths()
        for loc in list(locs.keys()):
            self.cb_location.addItem(loc)

        self.lo_settings.addWidget(self.l_location, row, 0)
        self.lo_settings.addWidget(self.cb_location, row, 1)
        if len(locs) < 2:
            self.l_location.setHidden(True)
            self.cb_location.setHidden(True)

        row += 1

        if self.core.mediaProducts.getLinkedToTasks():
            self.l_department = QLabel("Department:")
            self.e_department = QLineEdit()
            self.e_department.textEdited.connect(lambda x: self.enableOk())
            self.b_department = QToolButton()
            self.b_department.setArrowType(Qt.DownArrow)
            self.b_department.setMaximumSize(QSize(25, 16777215))
            self.b_department.clicked.connect(self.onDepartmentClicked)
            self.lo_settings.addWidget(self.l_department, row, 0)
            self.lo_settings.addWidget(self.e_department, row, 1)
            self.lo_settings.addWidget(self.b_department, row, 2)
            row += 1

            self.l_task = QLabel("Task:")
            self.e_task = QLineEdit()
            self.e_task.textEdited.connect(lambda x: self.enableOk())
            self.b_task = QToolButton()
            self.b_task.setArrowType(Qt.DownArrow)
            self.b_task.setMaximumSize(QSize(25, 16777215))
            self.b_task.clicked.connect(self.onTaskClicked)
            self.lo_settings.addWidget(self.l_task, row, 0)
            self.lo_settings.addWidget(self.e_task, row, 1)
            self.lo_settings.addWidget(self.b_task, row, 2)
            row += 1

            fileName = self.core.getCurrentFileName()
            context = self.core.getScenefileData(fileName)

            dep = context.get("department") or ""
            if self.entity.get("type") == "asset":
                departments = self.core.projects.getAssetDepartments()
            elif self.entity.get("type") == "shot":
                departments = self.core.projects.getShotDepartments()
            else:
                departments = []

            if not dep and departments:
                dep = departments[0]["abbreviation"]

            task = context.get("task") or ""
            if not task and dep:
                tasks = self.core.entities.getCategories(self.entity, dep)
                dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), dep)
                for dftTask in dftTasks:
                    if dftTask not in tasks:
                        tasks.append(dftTask)

                if tasks:
                    task = sorted(tasks, key=lambda x: x.lower())[0]

            self.e_department.setText(dep)
            self.e_task.setText(task)

        self.l_identifier = QLabel("Identifier:")
        self.e_identifier = QLineEdit()
        self.e_identifier.textEdited.connect(lambda x: self.enableOk())
        self.cb_identifierType = QComboBox()
        self.cb_identifierType.addItem("3D", "3drenders")
        self.cb_identifierType.addItem("2D", "2drenders")
        self.cb_identifierType.addItem("Playblast", "playblasts")
        self.cb_identifierType.addItem("External", "externalMedia")
        self.cb_identifierType.currentIndexChanged.connect(self.onMediaTypeChanged)
        self.w_identifier = QWidget()
        self.lo_identifier = QHBoxLayout(self.w_identifier)
        self.lo_identifier.setContentsMargins(0, 0, 0, 0)
        self.lo_identifier.addWidget(self.e_identifier)
        self.lo_identifier.addWidget(self.cb_identifierType)
        self.b_identifier = QToolButton()
        self.b_identifier.setArrowType(Qt.DownArrow)
        self.b_identifier.setMaximumSize(QSize(25, 16777215))
        self.b_identifier.clicked.connect(self.onIdentifierClicked)
        self.lo_settings.addWidget(self.l_identifier, row, 0)
        self.lo_settings.addWidget(self.w_identifier, row, 1)
        self.lo_settings.addWidget(self.b_identifier, row, 2)
        row += 1

        self.l_version = QLabel("Version:")
        self.sp_version = VersionSpinBox()
        self.sp_version.core = self.core
        self.sp_version.setRange(self.core.lowestVersion, 99999)
        self.b_version = QToolButton()
        self.b_version.setArrowType(Qt.DownArrow)
        self.b_version.setMaximumSize(QSize(25, 16777215))
        self.b_version.clicked.connect(self.onVersionClicked)
        self.lo_settings.addWidget(self.l_version, row, 0)
        self.lo_settings.addWidget(self.sp_version, row, 1)
        self.lo_settings.addWidget(self.b_version, row, 2)
        row += 1

        self.l_aov = QLabel("AOV:")
        self.e_aov = QLineEdit()
        self.e_aov.setText("rgb")
        self.e_aov.textEdited.connect(lambda x: self.enableOk())
        self.b_aov = QToolButton()
        self.b_aov.setArrowType(Qt.DownArrow)
        self.b_aov.setMaximumSize(QSize(25, 16777215))
        self.b_aov.clicked.connect(self.onAovClicked)
        self.lo_settings.addWidget(self.l_aov, row, 0)
        self.lo_settings.addWidget(self.e_aov, row, 1)
        self.lo_settings.addWidget(self.b_aov, row, 2)
        row += 1

        self.w_mediaPath = QWidget()
        self.w_mediaPath.setObjectName("mediaWidget")
        self.l_mediaPathLabel = QLabel("Media Path:")
        self.l_mediaPath = QLabel("< Click or Drag & Drop media >")
        self.l_mediaPath.setAlignment(Qt.AlignCenter)
        self.l_mediaPath.setCursor(Qt.PointingHandCursor)
        self.l_mediaPath.mouseReleaseEvent = self.mediaMouseClickEvent
        self.lo_mediaPath = QHBoxLayout(self.w_mediaPath)
        self.lo_mediaPath.setContentsMargins(0, 20, 0, 20)
        self.lo_mediaPath.addWidget(self.l_mediaPath)
        self.sa_mediaPath = QScrollArea()
        self.sa_mediaPath.setWidgetResizable(True)
        self.sa_mediaPath.setWidget(self.w_mediaPath)
        self.lo_settings.addWidget(self.l_mediaPathLabel, row, 0)
        self.lo_settings.addWidget(self.sa_mediaPath, row, 1, 1, 2)
        self.w_mediaPath.setAcceptDrops(True)
        self.w_mediaPath.dragEnterEvent = self.mediaDragEnterEvent
        self.w_mediaPath.dragMoveEvent = self.mediaDragMoveEvent
        self.w_mediaPath.dragLeaveEvent = self.mediaDragLeaveEvent
        self.w_mediaPath.dropEvent = self.mediaDropEvent

        row += 1

        self.w_action = QWidget()
        self.l_action = QLabel("Action:")
        self.rb_copy = QRadioButton("Copy")
        self.rb_move = QRadioButton("Move")
        self.rb_link = QRadioButton("Link")
        self.lo_action = QHBoxLayout(self.w_action)
        self.lo_action.setContentsMargins(0, 0, 0, 0)
        self.lo_action.addStretch()
        self.lo_action.addWidget(self.rb_copy)
        self.lo_action.addWidget(self.rb_move)
        self.lo_action.addWidget(self.rb_link)
        self.lo_settings.addWidget(self.l_action, row, 0)
        self.lo_settings.addWidget(self.w_action, row, 1, 1, 2)
        self.rb_copy.setChecked(True)
        row += 1

        self.bb_main = QDialogButtonBox()
        self.b_create = self.bb_main.addButton("Create", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.b_create.setEnabled(False)
        self.bb_main.accepted.connect(self.createClicked)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addWidget(self.w_settings)
        # self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def entityMouseClickEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                if getattr(self, "dlg_entity", None):
                    self.dlg_entity.close()

                self.dlg_entity = self.core.getStateManager().entityDlg(self)
                self.dlg_entity.w_entities.editEntitiesOnDclick = False
                self.dlg_entity.w_entities.navigate(self.entity)
                self.dlg_entity.entitySelected.connect(lambda x: self.setEntity(x))
                self.dlg_entity.show()

    @err_catcher(name=__name__)
    def setEntity(self, entity):
        self.entity = entity
        pmap = self.core.entities.getEntityPreview(self.entity)
        if not pmap:
            pmap = self.core.media.emptyPrvPixmap

        pmap = self.core.media.scalePixmap(pmap, 107, 60, fitIntoBounds=False, crop=True)
        self.l_entityPreview.setPixmap(pmap)
        entityName = "%s - %s" % (self.entity["type"].capitalize(), self.core.entities.getEntityName(self.entity))
        self.l_entityName.setText(entityName)

    @err_catcher(name=__name__)
    def setMediaPaths(self, paths):
        pathList = paths.split("\n")
        if len(pathList) == 1 and os.path.isdir(pathList[0]):
            mods = QApplication.keyboardModifiers()
            if mods != Qt.ControlModifier:
                pathList = [os.path.join(pathList[0], x) for x in os.listdir(pathList[0])]
                paths = "\n".join(sorted(pathList))

        self.l_mediaPath.setText(paths)
        self.enableOk()

    @err_catcher(name=__name__)
    def mediaMouseClickEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            tmenu = QMenu(self)

            tAct = QAction("Select File...", self)
            tAct.triggered.connect(self.browseFile)
            tmenu.addAction(tAct)

            tAct = QAction("Select Folder...", self)
            tAct.triggered.connect(self.browseFolder)
            tmenu.addAction(tAct)

            tAct = QAction("Copy", self)
            tAct.triggered.connect(lambda: self.core.copyToClipboard(self.l_mediaPath.text()))
            tmenu.addAction(tAct)

            tAct = QAction("Open in Explorer", self)
            tAct.triggered.connect(self.openFolder)
            tmenu.addAction(tAct)

            tAct = QAction("Clear", self)
            tAct.triggered.connect(self.clearMedia)
            tmenu.addAction(tAct)

            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def mediaDragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def mediaDragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
            self.w_mediaPath.setStyleSheet(
                "QWidget#mediaWidget { border-style: dashed; border-color: rgb(100, 200, 100);  border-width: 2px; }"
            )
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def mediaDragLeaveEvent(self, e):
        self.w_mediaPath.setStyleSheet("")

    @err_catcher(name=__name__)
    def mediaDropEvent(self, e):
        if e.mimeData().hasUrls():
            self.w_mediaPath.setStyleSheet("")
            e.setDropAction(Qt.LinkAction)
            e.accept()

            fname = [
                os.path.normpath(str(url.toLocalFile())) for url in e.mimeData().urls()
            ]
            self.setMediaPaths("\n".join(fname))
            self.enableOk()
        else:
            e.ignore()

    @err_catcher(name=__name__)
    def onMediaTypeChanged(self, idx=None):
        curType = self.cb_identifierType.currentData()
        self.l_aov.setHidden(curType != "3drenders")
        self.e_aov.setHidden(curType != "3drenders")
        self.b_aov.setHidden(curType != "3drenders")
        self.l_action.setHidden(curType != "externalMedia")
        self.w_action.setHidden(curType != "externalMedia")
        self.enableOk()

    @err_catcher(name=__name__)
    def onDepartmentClicked(self):
        tmenu = QMenu(self)

        if self.entity.get("type") == "asset":
            departments = self.core.projects.getAssetDepartments()
        elif self.entity.get("type") == "shot":
            departments = self.core.projects.getShotDepartments()
        else:
            departments = []

        for dep in departments:
            tAct = QAction(dep["abbreviation"], self)
            tAct.triggered.connect(lambda x=None, d=dep["abbreviation"]: self.e_department.setText(d))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onTaskClicked(self):
        tmenu = QMenu(self)

        tasks = self.core.entities.getCategories(self.entity, self.e_department.text())
        dftTasks = self.core.entities.getDefaultTasksForDepartment(self.entity.get("type"), self.e_department.text())
        for dftTask in dftTasks:
            if dftTask not in tasks:
                tasks.append(dftTask)

        if not tasks:
            return

        for task in sorted(tasks, key=lambda x: x.lower()):
            tAct = QAction(task, self)
            tAct.triggered.connect(lambda x=None, t=task: self.e_task.setText(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onIdentifierClicked(self):
        tmenu = QMenu(self)

        entity = self.entity.copy()
        if self.core.mediaProducts.getLinkedToTasks():
            entity["department"] = self.e_department.text()
            entity["task"] = self.e_task.text()

        idfs = self.core.mediaProducts.getIdentifiersByType(entity)
        idfNames = []
        for mtype in idfs:
            for idf in idfs[mtype]:
                name = idf["identifier"]
                idfNames.append(name)

        for idfName in sorted(set(idfNames)):
            tAct = QAction(idfName, self)
            tAct.triggered.connect(lambda x=None, t=idfName: self.e_identifier.setText(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onVersionClicked(self):
        tmenu = QMenu(self)

        entity = self.entity.copy()
        if self.core.mediaProducts.getLinkedToTasks():
            entity["department"] = self.e_department.text()
            entity["task"] = self.e_task.text()

        entity["identifier"] = self.e_identifier.text()
        entity["mediaType"] = self.cb_identifierType.currentData()
        versions = self.core.mediaProducts.getVersionsFromIdentifier(entity)
        for version in sorted(versions, key=lambda x: x["version"], reverse=True):
            name = version["version"]
            tAct = QAction(name, self)
            intVersion = self.core.products.getIntVersionFromVersionName(name)
            if intVersion is None:
                continue

            tAct.triggered.connect(lambda x=None, t=intVersion: self.sp_version.setValue(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def onAovClicked(self):
        tmenu = QMenu(self)

        entity = self.entity.copy()
        if self.core.mediaProducts.getLinkedToTasks():
            entity["department"] = self.e_department.text()
            entity["task"] = self.e_task.text()

        entity["identifier"] = self.e_identifier.text()
        entity["mediaType"] = self.cb_identifierType.currentData()
        entity["version"] = self.core.versionFormat % self.sp_version.value()
        aovs = self.core.mediaProducts.getAOVsFromVersion(entity)
        for aov in sorted(aovs, key=lambda x: x["aov"]):
            name = aov["aov"]
            tAct = QAction(name, self)
            tAct.triggered.connect(lambda x=None, t=name: self.e_aov.setText(t))
            tmenu.addAction(tAct)

        if not tmenu.isEmpty():
            tmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_identifier.textChanged.connect(lambda x: self.enableOk())

    @err_catcher(name=__name__)
    def browseFolder(self):
        curText = self.l_mediaPath.text()
        startpath = curText if curText and not curText.startswith("<") else self.core.projectPath
        selectedPath = QFileDialog.getExistingDirectory(
            self, "Select media folder", startpath
        )

        if selectedPath:
            self.setMediaPaths(selectedPath.replace("\\", "/"))

    @err_catcher(name=__name__)
    def browseFile(self):
        curText = self.l_mediaPath.text()
        startpath = curText if curText and not curText.startswith("<") else self.core.projectPath
        selectedFile = QFileDialog.getOpenFileName(
            self, "Select media file", startpath
        )[0]

        if selectedFile:
            self.setMediaPaths(selectedFile.replace("\\", "/"))

    @err_catcher(name=__name__)
    def openFolder(self):
        path = self.l_mediaPath.text()
        self.core.openFolder(path)

    @err_catcher(name=__name__)
    def clearMedia(self):
        self.setMediaPaths("< Click or Drag & Drop media >")

    @err_catcher(name=__name__)
    def enableOk(self):
        idfText = self.e_identifier.text()
        mediaText = self.l_mediaPath.text()
        mediaTextValid = bool(mediaText) and mediaText != "< Click or Drag & Drop media >"
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.e_department.text()
            taskText = self.e_task.text()
            valid = bool(idfText and mediaTextValid and depText and taskText)
        else:
            valid = bool(idfText and mediaTextValid)

        if self.cb_identifierType.currentData() == "3drenders":
            valid = valid and bool(self.e_aov.text())

        self.b_create.setEnabled(valid)

    @err_catcher(name=__name__)
    def createClicked(self):
        if self.core.mediaProducts.getLinkedToTasks():
            depText = self.core.validateLineEdit(self.e_department)
            if not depText:
                self.core.popup("Invalid department.")
                return

            taskText = self.core.validateLineEdit(self.e_task)
            if not taskText:
                self.core.popup("Invalid task.")
                return

        idfText = self.core.validateLineEdit(self.e_identifier)
        if not idfText:
            self.core.popup("Invalid identifier.")
            return

        if self.cb_identifierType.currentData() == "3drenders":
            aovText = self.core.validateLineEdit(self.e_aov)
            if not aovText:
                self.core.popup("Invalid aov.")
                return

        mediaText = self.l_mediaPath.text()
        if not mediaText or mediaText == "< Click or Drag & Drop media >":
            self.core.popup("Invalid media path.")
            return

        self.accept()


class VersionSpinBox(QSpinBox):
    def textFromValue(self, value):
        return self.core.versionFormat % value


class StateDefaults(QGroupBox):
    def __init__(self, origin, data=None):
        super(StateDefaults, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.core.parentWindow(self)
        self.items = []

        self.loadLayout()
        self.connectEvents()
        if data:
            self.loadStateData(data)

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.w_add = QWidget()
        self.b_add = QToolButton()
        self.lo_add = QHBoxLayout()
        self.w_add.setLayout(self.lo_add)
        self.lo_add.addStretch()
        self.lo_add.addWidget(self.b_add)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_add.setIcon(icon)
        self.b_add.setIconSize(QSize(20, 20))
        self.b_add.setToolTip("Add State Type")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_add.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reset.png"
        )
        icon = self.core.media.getColoredIcon(path)

        self.lo_items = QVBoxLayout()
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.lo_main.addLayout(self.lo_items)
        self.lo_main.addWidget(self.w_add)
        self.setTitle("State Defaults")

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_add.clicked.connect(self.onAddClicked)

    @err_catcher(name=__name__)
    def onAddClicked(self):
        pos = QCursor.pos()
        sm = self.core.getStateManager()
        if not sm:
            return

        menu = QMenu(self)
        typeNames = sm.getStateTypes()

        for typeName in typeNames:
            act = menu.addAction(typeName)
            act.triggered.connect(
                lambda x=None, typeName=typeName: self.addItem(
                    typeName
                )
            )

        if not menu.isEmpty():
            menu.exec_(pos)

    @err_catcher(name=__name__)
    def loadStateData(self, data):
        self.clearItems()
        for data in data:
            self.addItem(
                name=data["name"],
                dftTasks=data["dftTasks"],
                stateData=data["stateData"],
            )

    @err_catcher(name=__name__)
    def addItem(self, name=None, dftTasks=None, stateData=None):
        item = StateDefaultItem(self.origin, name)
        self.items.append(item)
        item.removed.connect(self.removeItem)
        item.signalItemDropped.connect(self.itemDropped)

        if name:
            item.setName(name)

        if dftTasks:
            item.setDftTasks(dftTasks)

        if stateData:
            item.setStateData(stateData)

        self.lo_items.addWidget(item)
        return item

    @err_catcher(name=__name__)
    def itemDropped(self, item):
        pos = QCursor.pos()
        targetItem = None
        for sitem in self.items:
            if sitem == item:
                continue

            rect = sitem.geometry()
            rpos = sitem.parent().mapFromGlobal(pos)
            if rect.contains(rpos):
                targetItem = sitem

        if targetItem:
            idx = self.lo_items.indexOf(item)
            targetIdx = self.lo_items.indexOf(targetItem)
            data = self.getItemData()
            itemData = data.pop(idx)
            data.insert(targetIdx, itemData)
            self.loadStateData(data)
        else:
            lo = self.lo_items
            widgets = [lo.itemAt(idx).widget() for idx in range(lo.count()) if lo.itemAt(idx).widget()]
            order = sorted(widgets, key=lambda i: i.pos().y())
            for idx, widget in enumerate(order):
                lo.takeAt(idx)
                lo.insertWidget(idx, widget)

    @err_catcher(name=__name__)
    def removeItem(self, item):
        self.items.remove(item)
        idx = self.lo_items.indexOf(item)
        if idx != -1:
            w = self.lo_items.takeAt(idx)
            if w.widget():
                w.widget().deleteLater()

    @err_catcher(name=__name__)
    def clearItems(self):
        for idx in reversed(range(self.lo_items.count())):
            item = self.lo_items.takeAt(idx)
            w = item.widget()
            if w:
                w.setVisible(False)
                w.deleteLater()

        self.items = []

    @err_catcher(name=__name__)
    def getItemData(self):
        itemData = []
        for idx in range(self.lo_items.count()):
            w = self.lo_items.itemAt(idx)
            widget = w.widget()
            if widget:
                if isinstance(widget, StateDefaultItem):
                    sdata = {
                        "name": widget.name(),
                        "dftTasks": widget.dftTasks(),
                        "stateData": widget.stateData(),
                    }
                    itemData.append(sdata)

        return itemData


class StateDefaultItem(QWidget):

    removed = Signal(object)
    signalItemDropped = Signal(object)

    def __init__(self, origin, typename):
        super(StateDefaultItem, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.typename = typename
        self.drag_start_pos = None
        self.loadLayout()
        self.setDftTasks({
            "entities": ["*"],
            "departments": ["*"],
            "tasks": ["*"],
            "useExpression": False,
            "expression": "# set the variable \"result\" to True or False to decide when the state settings should get applied.\n# Example:\n#\n# context = core.getScenefileData(core.getCurrentFileName())\n# if context.get(\"department\") == \"rig\":\n#     result = True\n# else:\n#     result = False",
        })

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_reorder = QLabel()
        self.l_reorder.setToolTip("Reorder")
        self.l_typeName = QLabel(self.typename)
        self.l_typeName.setToolTip("State Type")
        self.l_default = QLabel("Default for:")
        self.l_defaultEntity = QLabel()
        self.b_editDft = QToolButton()
        self.b_editDft.clicked.connect(self.editDefaultsClicked)
        self.b_editDft.setToolTip("Select for which tasks this state settings will be used as a default...")
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "edit.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_editDft.setIcon(icon)
        self.b_states = QToolButton()
        self.b_states.setToolTip("Configure state settings...")
        self.b_states.clicked.connect(self.configureStates)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reorder.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.l_reorder.setPixmap(icon.pixmap(20, 20))

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "configure.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_states.setIcon(icon)

        self.b_remove = QToolButton()
        self.b_remove.clicked.connect(lambda: self.removed.emit(self))

        self.lo_dft = QHBoxLayout()
        self.lo_dft.addWidget(self.l_default)
        self.lo_dft.addWidget(self.l_defaultEntity)
        self.lo_dft.addWidget(self.b_editDft)
        self.lo_dft.addStretch()
        self.lo_dft.setContentsMargins(0, 0, 0, 0)

        self.lo_main = QHBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)
        self.lo_main.addWidget(self.l_reorder)

        self.lo_main.addWidget(self.l_typeName, 10)
        self.lo_main.addWidget(self.b_states)
        self.lo_main.addLayout(self.lo_dft, 20)
        
        self.lo_main.addWidget(self.b_remove)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_remove.setIcon(icon)
        self.b_remove.setIconSize(QSize(20, 20))
        self.b_remove.setToolTip("Delete")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_remove.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

    @err_catcher(name=__name__)
    def editDefaultsClicked(self):
        self.dlg_defaults = DefaultTasksWindow(self)
        self.dlg_defaults.signalSaved.connect(self.setDftTasks)
        self.dlg_defaults.show()

    @err_catcher(name=__name__)
    def configureStates(self):
        stateType = self.name()
        import StateManager
        settings = self.stateData()
        dlg = StateManager.getStateWindow(self.core, stateType, settings=settings, connectBBox=False, parent=self)
        dlg.setWindowTitle("Default State Settings - %s" % stateType)
        dlg.bb_settings.buttons()[0].setText("Save")
        dlg.adjustSize()
        dlg.resize(dlg.width(), dlg.height() + 20)
        dlg.bb_settings.accepted.connect(lambda d=dlg: self.onStateSaveClicked(d))
        dlg.bb_settings.rejected.connect(dlg.reject)
        dlg.show()

    @err_catcher(name=__name__)
    def onStateSaveClicked(self, dlg):
        self.setStateData(dlg.stateItem.ui.getStateProps())
        dlg.close()

    @err_catcher(name=__name__)
    def name(self):
        return self.l_typeName.text()

    @err_catcher(name=__name__)
    def setName(self, name):
        return self.l_typeName.setText(name)

    @err_catcher(name=__name__)
    def dftTasks(self):
        return self._dftTasks

    @err_catcher(name=__name__)
    def setDftTasks(self, tasks):
        self._dftTasks = tasks
        entities = ", ".join(self._dftTasks["entities"])
        departments = ", ".join(self._dftTasks["departments"])
        tasks = ", ".join(self._dftTasks["tasks"])
        if len(self._dftTasks["entities"]) > 1:
            dataStr = "%s\n%s\n%s" % (entities, departments, tasks)
        else:
            dataStr = "%s - %s - %s" % (entities, departments, tasks)

        if dataStr == " -  - ":
            dataStr = "-"

        if self._dftTasks.get("useExpression") and self._dftTasks.get("expression"):
            dataStr += " + expression"

        self.l_defaultEntity.setText(dataStr)

    @err_catcher(name=__name__)
    def stateData(self):
        return getattr(self, "_stateData", None)

    @err_catcher(name=__name__)
    def setStateData(self, stateData):
        self._stateData = stateData

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None:
            # While left button is clicked the widget will move along with the mouse
            self.move(self.pos() + event.pos() - self.drag_start_pos)
        super(StateDefaultItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_start_pos is None:
            return

        self.setCursor(Qt.ArrowCursor)
        super(StateDefaultItem, self).mouseReleaseEvent(event)
        if (self.pos() + self.drag_start_pos) != QCursor.pos():
            self.signalItemDropped.emit(self)
        self.drag_start_pos = None

    @err_catcher(name=__name__)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.drag_start_pos = event.pos()
            self.raise_()

        super(StateDefaultItem, self).mousePressEvent(event)


class StatePresets(QGroupBox):
    def __init__(self, origin, data=None):
        super(StatePresets, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.core.parentWindow(self)
        self.items = []

        self.loadLayout()
        self.connectEvents()
        if data:
            self.loadPresetData(data)

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.w_add = QWidget()
        self.b_add = QToolButton()
        self.lo_add = QHBoxLayout()
        self.w_add.setLayout(self.lo_add)
        self.lo_add.addStretch()
        self.lo_add.addWidget(self.b_add)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_add.setIcon(icon)
        self.b_add.setIconSize(QSize(20, 20))
        self.b_add.setToolTip("Add Preset")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_add.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reset.png"
        )
        icon = self.core.media.getColoredIcon(path)

        self.lo_items = QVBoxLayout()
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.lo_main.addLayout(self.lo_items)
        self.lo_main.addWidget(self.w_add)
        self.setTitle("State Presets")

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_add.clicked.connect(self.addItem)

    @err_catcher(name=__name__)
    def loadPresetData(self, data):
        self.clearItems()
        for data in data:
            self.addItem(
                name=data["name"],
                dftTasks=data["dftTasks"],
                states=data["states"],
            )

    @err_catcher(name=__name__)
    def addItem(self, name=None, dftTasks=None, states=None):
        item = PresetItem(self.origin)
        self.items.append(item)
        item.removed.connect(self.removeItem)
        item.signalItemDropped.connect(self.itemDropped)

        if name:
            item.setName(name)

        if dftTasks:
            item.setDftTasks(dftTasks)

        if states:
            item.setStates(states)

        self.lo_items.addWidget(item)
        return item

    @err_catcher(name=__name__)
    def itemDropped(self, item):
        pos = QCursor.pos()
        targetItem = None
        for sitem in self.items:
            if sitem == item:
                continue

            rect = sitem.geometry()
            rpos = sitem.parent().mapFromGlobal(pos)
            if rect.contains(rpos):
                targetItem = sitem

        if targetItem:
            idx = self.lo_items.indexOf(item)
            targetIdx = self.lo_items.indexOf(targetItem)
            data = self.getItemData()
            itemData = data.pop(idx)
            data.insert(targetIdx, itemData)
            self.loadPresetData(data)
        else:
            lo = self.lo_items
            widgets = [lo.itemAt(idx).widget() for idx in range(lo.count()) if lo.itemAt(idx).widget()]
            order = sorted(widgets, key=lambda i: i.pos().y())
            for idx, widget in enumerate(order):
                lo.takeAt(idx)
                lo.insertWidget(idx, widget)

    @err_catcher(name=__name__)
    def removeItem(self, item):
        self.items.remove(item)
        idx = self.lo_items.indexOf(item)
        if idx != -1:
            w = self.lo_items.takeAt(idx)
            if w.widget():
                w.widget().deleteLater()

    @err_catcher(name=__name__)
    def clearItems(self):
        for idx in reversed(range(self.lo_items.count())):
            item = self.lo_items.takeAt(idx)
            w = item.widget()
            if w:
                w.setVisible(False)
                w.deleteLater()

        self.items = []

    @err_catcher(name=__name__)
    def getItemData(self):
        itemData = []
        for idx in range(self.lo_items.count()):
            w = self.lo_items.itemAt(idx)
            widget = w.widget()
            if widget:
                if isinstance(widget, PresetItem):
                    sdata = {
                        "name": widget.name(),
                        "dftTasks": widget.dftTasks(),
                        "states": widget.states(),
                    }
                    itemData.append(sdata)

        return itemData


class PresetItem(QWidget):

    removed = Signal(object)
    signalItemDropped = Signal(object)

    def __init__(self, origin):
        super(PresetItem, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.drag_start_pos = None
        self.loadLayout()
        self.setDftTasks({
            "entities": [],
            "departments": [],
            "tasks": [],
            "useExpression": False,
            "expression": "# set the variable \"result\" to True or False to decide when the preset should get applied.\n# Example:\n#\n# context = core.getScenefileData(core.getCurrentFileName())\n# if context.get(\"department\") == \"rig\":\n#     result = True\n# else:\n#     result = False",
        })

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_reorder = QLabel()
        self.l_reorder.setToolTip("Reorder")
        self.l_name = QLabel("    Name:")
        self.e_name = QLineEdit()
        self.e_name.setPlaceholderText("Name")
        self.e_name.setToolTip("Name")
        self.l_default = QLabel("Default for:")
        self.l_defaultEntity = QLabel()
        self.b_editDft = QToolButton()
        self.b_editDft.clicked.connect(self.editDefaultsClicked)
        self.b_editDft.setToolTip("Select for which tasks this preset will be used as a default...")
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "edit.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_editDft.setIcon(icon)
        self.l_states = QLabel("    States:")
        self.b_states = QToolButton()
        self.b_states.setToolTip("Configure states...")
        self.b_states.clicked.connect(self.configureStates)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reorder.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.l_reorder.setPixmap(icon.pixmap(20, 20))

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "configure.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_states.setIcon(icon)

        self.b_remove = QToolButton()
        self.b_remove.clicked.connect(lambda: self.removed.emit(self))

        self.lo_dft = QHBoxLayout()
        self.lo_dft.addWidget(self.l_default)
        self.lo_dft.addWidget(self.l_defaultEntity)
        self.lo_dft.addWidget(self.b_editDft)
        self.lo_dft.addStretch()
        self.lo_dft.setContentsMargins(0, 0, 0, 0)

        self.lo_main = QHBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)
        self.lo_main.addWidget(self.l_reorder)

        # self.lo_main.addWidget(self.l_name)
        self.lo_main.addWidget(self.e_name, 10)
        # self.lo_main.addWidget(self.l_states)
        self.lo_main.addWidget(self.b_states)
        self.lo_main.addLayout(self.lo_dft, 20)
        
        self.lo_main.addWidget(self.b_remove)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_remove.setIcon(icon)
        self.b_remove.setIconSize(QSize(20, 20))
        self.b_remove.setToolTip("Delete")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_remove.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

    @err_catcher(name=__name__)
    def editDefaultsClicked(self):
        self.dlg_defaults = DefaultTasksWindow(self)
        self.dlg_defaults.signalSaved.connect(self.setDftTasks)
        self.dlg_defaults.show()

    @err_catcher(name=__name__)
    def configureStates(self):
        if hasattr(self, "smPreset") and self.smPreset.isVisible():
            self.smPreset.close()

        windowTitle = "State Preset - %s" % self.name()
        self.smPreset = self.core.stateManager(openUi=False, new_instance=True, standalone=True)
        self.smPreset.setWindowTitle(windowTitle)
        self.smPreset.gb_publish.setHidden(True)
        self.smPreset.bb_main = QDialogButtonBox()
        self.smPreset.bb_main.addButton("Save", QDialogButtonBox.AcceptRole)
        self.smPreset.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.smPreset.bb_main.accepted.connect(lambda: self.onStateManagerSaveClicked(self.smPreset))
        self.smPreset.bb_main.rejected.connect(self.smPreset.close)
        self.smPreset.centralwidget.layout().addWidget(self.smPreset.bb_main)
        self.smPreset.centralwidget.layout().setContentsMargins(0, 9, 9, 9)
        if self.states():
            self.smPreset.loadStates(self.states())

        self.smPreset.show()

    @err_catcher(name=__name__)
    def onStateManagerSaveClicked(self, sm):
        self.setStates(sm.getStateSettings())
        sm.close()

    @err_catcher(name=__name__)
    def name(self):
        return self.e_name.text()

    @err_catcher(name=__name__)
    def setName(self, name):
        return self.e_name.setText(name)

    @err_catcher(name=__name__)
    def dftTasks(self):
        return self._dftTasks

    @err_catcher(name=__name__)
    def setDftTasks(self, tasks):
        self._dftTasks = tasks
        entities = ", ".join(self._dftTasks["entities"])
        departments = ", ".join(self._dftTasks["departments"])
        tasks = ", ".join(self._dftTasks["tasks"])
        if len(self._dftTasks["entities"]) > 1:
            dataStr = "%s\n%s\n%s" % (entities, departments, tasks)
        else:
            dataStr = "%s - %s - %s" % (entities, departments, tasks)

        if dataStr == " -  - ":
            dataStr = "-"

        if self._dftTasks.get("useExpression") and self._dftTasks.get("expression"):
            dataStr += " + expression"

        self.l_defaultEntity.setText(dataStr)

    @err_catcher(name=__name__)
    def states(self):
        return getattr(self, "_states", None)

    @err_catcher(name=__name__)
    def setStates(self, states):
        self._states = states

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None:
            # While left button is clicked the widget will move along with the mouse
            self.move(self.pos() + event.pos() - self.drag_start_pos)
        super(PresetItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_start_pos is None:
            return

        self.setCursor(Qt.ArrowCursor)
        super(PresetItem, self).mouseReleaseEvent(event)
        if (self.pos() + self.drag_start_pos) != QCursor.pos():
            self.signalItemDropped.emit(self)
        self.drag_start_pos = None

    @err_catcher(name=__name__)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.drag_start_pos = event.pos()
            self.raise_()

        super(PresetItem, self).mousePressEvent(event)


class DefaultPresetScenes(QGroupBox):
    def __init__(self, origin, data=None):
        super(DefaultPresetScenes, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.core.parentWindow(self)
        self.items = []

        self.loadLayout()
        self.connectEvents()
        if data:
            self.loadPresetData(data)

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.w_add = QWidget()
        self.b_add = QToolButton()
        self.lo_add = QHBoxLayout()
        self.w_add.setLayout(self.lo_add)
        self.lo_add.addStretch()
        self.lo_add.addWidget(self.b_add)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_add.setIcon(icon)
        self.b_add.setIconSize(QSize(20, 20))
        self.b_add.setToolTip("Add Preset")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_add.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reset.png"
        )
        icon = self.core.media.getColoredIcon(path)

        self.lo_items = QVBoxLayout()
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.lo_main.addLayout(self.lo_items)
        self.lo_main.addWidget(self.w_add)
        self.setTitle("Default Preset Scenefiles")

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.b_add.clicked.connect(self.addItem)

    @err_catcher(name=__name__)
    def loadPresetData(self, data):
        self.clearItems()
        for data in data:
            self.addItem(
                name=data["name"],
                dftTasks=data["dftTasks"],
            )

    @err_catcher(name=__name__)
    def addItem(self, name=None, dftTasks=None):
        item = DefaultPresetScenesItem(self.origin)
        self.items.append(item)
        item.removed.connect(self.removeItem)
        item.signalItemDropped.connect(self.itemDropped)

        if name:
            item.setName(name)

        if dftTasks:
            item.setDftTasks(dftTasks)

        self.lo_items.addWidget(item)
        return item

    @err_catcher(name=__name__)
    def itemDropped(self, item):
        pos = QCursor.pos()
        targetItem = None
        for sitem in self.items:
            if sitem == item:
                continue

            rect = sitem.geometry()
            rpos = sitem.parent().mapFromGlobal(pos)
            if rect.contains(rpos):
                targetItem = sitem

        if targetItem:
            idx = self.lo_items.indexOf(item)
            targetIdx = self.lo_items.indexOf(targetItem)
            data = self.getItemData()
            itemData = data.pop(idx)
            data.insert(targetIdx, itemData)
            self.loadPresetData(data)
        else:
            lo = self.lo_items
            widgets = [lo.itemAt(idx).widget() for idx in range(lo.count()) if lo.itemAt(idx).widget()]
            order = sorted(widgets, key=lambda i: i.pos().y())
            for idx, widget in enumerate(order):
                lo.takeAt(idx)
                lo.insertWidget(idx, widget)

    @err_catcher(name=__name__)
    def removeItem(self, item):
        self.items.remove(item)
        idx = self.lo_items.indexOf(item)
        if idx != -1:
            w = self.lo_items.takeAt(idx)
            if w.widget():
                w.widget().deleteLater()

    @err_catcher(name=__name__)
    def clearItems(self):
        for idx in reversed(range(self.lo_items.count())):
            item = self.lo_items.takeAt(idx)
            w = item.widget()
            if w:
                w.setVisible(False)
                w.deleteLater()

        self.items = []

    @err_catcher(name=__name__)
    def getItemData(self):
        itemData = []
        for idx in range(self.lo_items.count()):
            w = self.lo_items.itemAt(idx)
            widget = w.widget()
            if widget:
                if isinstance(widget, DefaultPresetScenesItem):
                    sdata = {
                        "name": widget.name(),
                        "dftTasks": widget.dftTasks(),
                    }
                    itemData.append(sdata)

        return itemData


class DefaultPresetScenesItem(QWidget):

    removed = Signal(object)
    signalItemDropped = Signal(object)

    def __init__(self, origin):
        super(DefaultPresetScenesItem, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.drag_start_pos = None
        self.loadLayout()
        self.setDftTasks({
            "entities": ["*"],
            "departments": ["*"],
            "tasks": ["*"],
            "useExpression": False,
            "expression": "# set the variable \"result\" to True or False to decide when the default preset scenefile should get applied.\n# Example:\n#\n# context = core.getScenefileData(core.getCurrentFileName())\n# if context.get(\"department\") == \"rig\":\n#     result = True\n# else:\n#     result = False",
        })

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_reorder = QLabel()
        self.l_reorder.setToolTip("Reorder")
        self.e_name = QLineEdit()
        self.e_name.setPlaceholderText("Preset Scenefile")
        self.e_name.setToolTip("Preset Scenefile")
        self.l_default = QLabel("Default for:")
        self.l_defaultEntity = QLabel()
        self.b_editDft = QToolButton()
        self.b_editDft.clicked.connect(self.editDefaultsClicked)
        self.b_editDft.setToolTip("Select for which tasks this preset will be used as a default...")
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "edit.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_editDft.setIcon(icon)
        self.b_presets = QToolButton()
        self.b_presets.setToolTip("Select available preset...")
        self.b_presets.clicked.connect(self.showPresets)

        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "reorder.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.l_reorder.setPixmap(icon.pixmap(20, 20))
        self.b_presets.setArrowType(Qt.DownArrow)

        self.b_remove = QToolButton()
        self.b_remove.clicked.connect(lambda: self.removed.emit(self))

        self.lo_dft = QHBoxLayout()
        self.lo_dft.addWidget(self.l_default)
        self.lo_dft.addWidget(self.l_defaultEntity)
        self.lo_dft.addWidget(self.b_editDft)
        self.lo_dft.addStretch()
        self.lo_dft.setContentsMargins(0, 0, 0, 0)

        self.lo_main = QHBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)
        self.lo_main.addWidget(self.l_reorder)

        self.lo_main.addWidget(self.e_name, 10)
        self.lo_main.addWidget(self.b_presets)
        self.lo_main.addLayout(self.lo_dft, 20)
        
        self.lo_main.addWidget(self.b_remove)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_remove.setIcon(icon)
        self.b_remove.setIconSize(QSize(20, 20))
        self.b_remove.setToolTip("Delete")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_remove.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

    @err_catcher(name=__name__)
    def editDefaultsClicked(self):
        self.dlg_defaults = DefaultTasksWindow(self)
        self.dlg_defaults.signalSaved.connect(self.setDftTasks)
        self.dlg_defaults.show()

    @err_catcher(name=__name__)
    def showPresets(self):
        pos = QCursor.pos()
        emp = QMenu(self)
        scenes = self.core.entities.getPresetScenes()
        dirMenus = {}
        for scene in sorted(scenes, key=lambda x: os.path.basename(x["label"]).lower()):
            folders = scene["label"].split("/")
            curPath = ""
            for idx, folder in enumerate(folders):
                if idx == (len(folders) - 1):
                    empAct = QAction(folder, self)
                    empAct.triggered.connect(
                        lambda y=None, fname=scene: self.e_name.setText(fname["label"])
                    )
                    dirMenus.get(curPath, emp).addAction(empAct)
                else:
                    curMenu = dirMenus.get(curPath, emp)
                    curPath = os.path.join(curPath, folder)
                    if curPath not in dirMenus:
                        dirMenus[curPath] = QMenu(folder, self)
                        curMenu.addMenu(dirMenus[curPath])

        if not emp.isEmpty():
            emp.exec_(pos)

    @err_catcher(name=__name__)
    def name(self):
        return self.e_name.text()

    @err_catcher(name=__name__)
    def setName(self, name):
        return self.e_name.setText(name)

    @err_catcher(name=__name__)
    def dftTasks(self):
        return self._dftTasks

    @err_catcher(name=__name__)
    def setDftTasks(self, tasks):
        self._dftTasks = tasks
        entities = ", ".join(self._dftTasks["entities"])
        departments = ", ".join(self._dftTasks["departments"])
        tasks = ", ".join(self._dftTasks["tasks"])
        if len(self._dftTasks["entities"]) > 1:
            dataStr = "%s\n%s\n%s" % (entities, departments, tasks)
        else:
            dataStr = "%s - %s - %s" % (entities, departments, tasks)

        if dataStr == " -  - ":
            dataStr = "-"

        if self._dftTasks.get("useExpression") and self._dftTasks.get("expression"):
            dataStr += " + expression"

        self.l_defaultEntity.setText(dataStr)

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None:
            # While left button is clicked the widget will move along with the mouse
            self.move(self.pos() + event.pos() - self.drag_start_pos)
        super(DefaultPresetScenesItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_start_pos is None:
            return

        self.setCursor(Qt.ArrowCursor)
        super(DefaultPresetScenesItem, self).mouseReleaseEvent(event)
        if (self.pos() + self.drag_start_pos) != QCursor.pos():
            self.signalItemDropped.emit(self)
        self.drag_start_pos = None

    @err_catcher(name=__name__)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.drag_start_pos = event.pos()
            self.raise_()

        super(DefaultPresetScenesItem, self).mousePressEvent(event)


class DefaultTasksWindow(QDialog):

    signalSaved = Signal(object)

    def __init__(self, origin):
        super(DefaultTasksWindow, self).__init__()
        self.origin = origin
        self.core = self.origin.core
        self.core.parentWindow(self, parent=origin)

        self.setupUi()
        self.loadData()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(800, 200)

    @err_catcher(name=__name__)
    def setupUi(self):
        self.setWindowTitle("Edit Tasks - %s" % self.origin.name())
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        self.lo_widgets = QGridLayout()
        self.l_entities = QLabel("Entities:")
        self.e_entities = QLineEdit()
        self.e_entities.setToolTip("Comma separated list of entities, e.g. \"asset:char/John, shot:seq1-shot010\", use \"*\" to select entities using a wildcard")
        self.b_entities = QToolButton()
        self.b_entities.setArrowType(Qt.DownArrow)
        self.b_entities.setToolTip("Select entities...")
        self.b_entities.clicked.connect(self.onEntitiesClicked)
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "help.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        pixmap = icon.pixmap(20, 20)
        self.l_previewEntity = HelpLabel(self)
        self.l_previewEntity.setPixmap(pixmap)
        self.l_previewEntity.setMouseTracking(True)
        self.l_previewEntity.getToolTip = self.getEntityToolTip

        self.l_departments = QLabel("Departments:")
        self.e_departments = QLineEdit()
        self.e_departments.setToolTip("Comma separated list of department names, e.g. \"anm, fx\", use \"*\" to select departments using a wildcard")
        self.b_departments = QToolButton()
        self.b_departments.setArrowType(Qt.DownArrow)
        self.b_departments.setToolTip("Select departments")
        self.b_departments.clicked.connect(self.onDepartmentsClicked)
        self.l_previewDepartment = HelpLabel(self)
        self.l_previewDepartment.setPixmap(pixmap)
        self.l_previewDepartment.setMouseTracking(True)
        self.l_previewDepartment.getToolTip = self.getDepartmentToolTip

        self.l_tasks = QLabel("Tasks:")
        self.e_tasks = QLineEdit()
        self.e_tasks.setToolTip("Comma separated list of task names, e.g. \"Animation, Lighting\", use \"*\" to select tasks using a wildcard")
        self.b_tasks = QToolButton()
        self.b_tasks.setArrowType(Qt.DownArrow)
        self.b_tasks.setToolTip("Select tasks")
        self.b_tasks.clicked.connect(self.onTasksClicked)
        self.l_previewTasks = HelpLabel(self)
        self.l_previewTasks.setPixmap(pixmap)
        self.l_previewTasks.setMouseTracking(True)
        self.l_previewTasks.getToolTip = self.getTaskToolTip

        self.chb_expression = QCheckBox("Python Expression")
        self.chb_expression.toggled.connect(self.expressionToggled)
        self.te_expression = QTextEdit()
        self.te_expression.setVisible(False)

        self.lo_widgets.addWidget(self.l_entities, 0, 0)
        self.lo_widgets.addWidget(self.e_entities, 0, 1)
        self.lo_widgets.addWidget(self.b_entities, 0, 2)
        self.lo_widgets.addWidget(self.l_previewEntity, 0, 3)
        self.lo_widgets.addWidget(self.l_departments, 1, 0)
        self.lo_widgets.addWidget(self.e_departments, 1, 1)
        self.lo_widgets.addWidget(self.b_departments, 1, 2)
        self.lo_widgets.addWidget(self.l_previewDepartment, 1, 3)
        self.lo_widgets.addWidget(self.l_tasks, 2, 0)
        self.lo_widgets.addWidget(self.e_tasks, 2, 1)
        self.lo_widgets.addWidget(self.b_tasks, 2, 2)
        self.lo_widgets.addWidget(self.l_previewTasks, 2, 3)
        self.lo_widgets.addWidget(self.chb_expression, 3, 1, 1, 3)
        self.lo_widgets.addWidget(self.te_expression, 4, 1, 1, 3)

        self.lo_main.addLayout(self.lo_widgets)
        self.lo_main.addStretch()

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Save", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)

        self.bb_main.accepted.connect(self.onSaveClicked)
        self.bb_main.rejected.connect(self.reject)
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def expressionToggled(self, state):
        self.te_expression.setVisible(state)
        if state:
            self.resize(self.width(), self.height()+200)
        else:
            self.resize(self.width(), 0)

    @property
    def projectEntities(self):
        if not hasattr(self, "_prjEntities"):
            assets = self.core.entities.getAssets()
            shots = self.core.entities.getShots()
            self._prjEntities = assets + shots

        return self._prjEntities

    @err_catcher(name=__name__)
    def getValidEntities(self):
        entities = [x.strip() for x in self.e_entities.text().split(",")]
        validEntities = []
        prjEntities = self.projectEntities
        addedEntityNames = []
        for entity in entities:
            for prjEntity in prjEntities:
                if entity != "*":
                    entityData = entity.split(":")
                    if entityData[0] != "*" and prjEntity.get("type") != entityData[0]:
                        continue

                    entityName = re.escape(entityData[1]).replace("\\*", ".*")
                    if prjEntity["type"] == "asset":
                        if not re.match("^%s$" % entityName, prjEntity.get("asset_path")):
                            continue

                    elif prjEntity["type"] == "shot":
                        if not re.match("^%s$" % entityName, self.core.entities.getShotName(prjEntity)):
                            continue

                entityName = self.core.entities.getEntityName(prjEntity)
                if entityName not in addedEntityNames:
                    validEntities.append(prjEntity)
                    addedEntityNames.append(entityName)

        return validEntities

    @err_catcher(name=__name__)
    def getEntityToolTip(self):
        entities = self.getValidEntities()
        tooltip = ""
        entityNames = {"assets": [], "shots": []}
        for entity in entities:
            if entity.get("type") == "asset":
                if entity.get("asset_path"):
                    entityNames["assets"].append(entity["asset_path"])
            elif entity.get("type") == "shot":
                if entity.get("shot"):
                    entityNames["shots"].append(self.core.entities.getShotName(entity))

        tooltip = "Assets:\n"
        for asset in entityNames["assets"]:
            tooltip += asset + "\n"

        tooltip += "\nShots:\n"
        for shot in entityNames["shots"]:
            tooltip += shot + "\n"

        return tooltip

    @err_catcher(name=__name__)
    def onEntitiesClicked(self):
        dlg = EntityDlg(self)
        dlg.entitiesSelected.connect(self.setEntities)
        validEntities = self.getValidEntities()
        if validEntities:
            dlg.w_entities.navigate(validEntities)

        dlg.exec_()

    @err_catcher(name=__name__)
    def setEntities(self, entities):
        entityNames = []
        for entity in entities:
            if entity["type"] == "asset":
                if not entity.get("asset_path"):
                    continue
                
                entityName = "asset:%s" % entity["asset_path"]
            elif entity["type"] == "shot":
                if not entity.get("shot"):
                    continue

                entityName = "shot:%s" % self.core.entities.getShotName(entity)
            
            entityNames.append(entityName)

        entityStr = ", ".join(entityNames)
        self.e_entities.setText(entityStr)

    @err_catcher(name=__name__)
    def getAvailableDepartments(self):
        validEntities = self.getValidEntities()
        departments = []
        for entity in validEntities:
            departments += self.core.entities.getSteps(entity)

        departments = sorted(set(departments))
        return departments

    @err_catcher(name=__name__)
    def getValidDepartments(self):
        validDeps = []
        deps = [p.strip() for p in self.e_departments.text().split(",") if p]
        prjDeps = self.getAvailableDepartments()
        for dep in deps:
            for prjDep in prjDeps:
                if dep != "*":
                    depName = re.escape(dep).replace("\\*", ".*")
                    if not re.match("^%s$" % depName, prjDep):
                        continue

                if prjDep not in validDeps:
                    validDeps.append(prjDep)

        return validDeps

    @err_catcher(name=__name__)
    def getDepartmentToolTip(self):
        deps = self.getValidDepartments()
        tooltip = ""
        for dep in deps:
            tooltip += dep + "\n"

        return tooltip

    @err_catcher(name=__name__)
    def onDepartmentsClicked(self):
        pos = QCursor.pos()
        menu = QMenu(self)

        deps = self.getAvailableDepartments()
        for dep in deps:
            exp = QAction(dep, self)
            exp.triggered.connect(lambda x=None, d=dep: self.toggleDepartment(d))
            menu.addAction(exp)

        if not menu.isEmpty():
            menu.exec_(pos)

    @err_catcher(name=__name__)
    def toggleDepartment(self, dep):
        deps = self.getValidDepartments()
        if dep in deps:
            deps.remove(dep)
        else:
            deps.append(dep)

        self.e_departments.setText(", ".join(deps))

    @err_catcher(name=__name__)
    def getAvailableTasks(self):
        validEntities = self.getValidEntities()
        departments = self.getValidDepartments()
        tasks = []
        for entity in validEntities:
            for department in departments:
                tasks += self.core.entities.getCategories(entity, step=department)

        tasks = sorted(set(tasks))
        return tasks

    @err_catcher(name=__name__)
    def getValidTasks(self):
        validTasks = []
        tasks = [p.strip() for p in self.e_tasks.text().split(",") if p]
        prjTasks = self.getAvailableTasks()
        for task in tasks:
            for prjTask in prjTasks:
                if task != "*":
                    taskName = re.escape(task).replace("\\*", ".*")
                    if not re.match("^%s$" % taskName, prjTask):
                        continue

                if prjTask not in validTasks:
                    validTasks.append(prjTask)

        return validTasks

    @err_catcher(name=__name__)
    def getTaskToolTip(self):
        tasks = self.getValidTasks()
        tooltip = ""
        for task in tasks:
            tooltip += task + "\n"

        return tooltip

    @err_catcher(name=__name__)
    def onTasksClicked(self):
        pos = QCursor.pos()
        menu = QMenu(self)

        tasks = self.getAvailableTasks()
        for task in tasks:
            exp = QAction(task, self)
            exp.triggered.connect(lambda x=None, t=task: self.toggleTasks(t))
            menu.addAction(exp)

        if not menu.isEmpty():
            menu.exec_(pos)

    @err_catcher(name=__name__)
    def toggleTasks(self, task):
        tasks = [t.strip() for t in self.e_tasks.text().split(",") if t]
        if task in tasks:
            tasks.remove(task)
        else:
            tasks.append(task)

        self.e_tasks.setText(", ".join(tasks))

    @err_catcher(name=__name__)
    def loadData(self):
        entities = ", ".join(self.origin.dftTasks()["entities"])
        departments = ", ".join(self.origin.dftTasks()["departments"])
        tasks = ", ".join(self.origin.dftTasks()["tasks"])
        useExpression = self.origin.dftTasks().get("useExpression", False)
        expression = self.origin.dftTasks().get("expression", "")

        self.e_entities.setText(entities)
        self.e_departments.setText(departments)
        self.e_tasks.setText(tasks)
        self.chb_expression.setChecked(useExpression)
        self.te_expression.setPlainText(expression)

    @err_catcher(name=__name__)
    def getData(self):
        data = {}
        data["entities"] = [x.strip() for x in self.e_entities.text().split(",")]
        data["departments"] = [x.strip() for x in self.e_departments.text().split(",")]
        data["tasks"] = [x.strip() for x in self.e_tasks.text().split(",")]
        data["useExpression"] = self.chb_expression.isChecked()
        data["expression"] = self.te_expression.toPlainText()
        return data

    @err_catcher(name=__name__)
    def onSaveClicked(self):
        data = self.getData()
        if data["useExpression"]:
            result = self.core.entities.validateExpression(data["expression"])
            if not result or not result["valid"]:
                msg = "Invalid expression."
                if result and result.get("error"):
                    msg += "\n\n%s" % result["error"]

                self.core.popup(msg)
                return

        self.signalSaved.emit(data)
        self.accept()


class HelpLabel(QLabel):

    signalEntered = Signal(object)

    def __init__(self, parent):
        super(HelpLabel, self).__init__()
        self.parent = parent

    def enterEvent(self, event):
        self.signalEntered.emit(self)

    def mouseMoveEvent(self, event):
        QToolTip.showText(QCursor.pos(), self.getToolTip())


class EntityDlg(QDialog):

    entitiesSelected = Signal(object)

    def __init__(self, origin, parent=None):
        super(EntityDlg, self).__init__()
        self.origin = origin
        self.parentDlg = parent
        self.core = self.origin.core
        self.setupUi()

    @err_catcher(name=__name__)
    def setupUi(self):
        title = "Select entity"

        self.setWindowTitle(title)
        self.core.parentWindow(self, parent=self.parentDlg)

        import EntityWidget
        self.w_entities = EntityWidget.EntityWidget(core=self.core, refresh=True)
        self.w_entities.editEntitiesOnDclick = False
        self.w_entities.getPage("Assets").tw_tree.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.w_entities.getPage("Shots").tw_tree.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.w_entities.getPage("Assets").setSearchVisible(False)
        self.w_entities.getPage("Shots").setSearchVisible(False)

        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Select", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Close", QDialogButtonBox.RejectRole)

        self.bb_main.clicked.connect(self.buttonClicked)

        self.lo_main.addWidget(self.w_entities)
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def itemDoubleClicked(self, item, column):
        self.buttonClicked("select")

    @err_catcher(name=__name__)
    def buttonClicked(self, button):
        if button == "select" or button.text() == "Select":
            entities = self.w_entities.getCurrentData(returnOne=False)
            if isinstance(entities, dict):
                entities = [entities]

            validEntities = []
            for entity in entities:
                if entity.get("type", "") not in ["asset", "shot"]:
                    continue

                validEntities.append(entity)

            if not validEntities:
                msg = "Invalid entity selected."
                self.core.popup(msg, parent=self)
                return

            self.entitiesSelected.emit(validEntities)

        self.close()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(400, 400)


class DefaultSettingItem(QWidget):

    def __init__(self, origin, name=None, dftTasks=None):
        super(DefaultSettingItem, self).__init__()
        self.core = origin.core
        self.drag_start_pos = None
        self.loadLayout()
        self.setName(name)
        self.setDftTasks(dftTasks)

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_name = QLabel()
        self.l_default = QLabel("Apply to tasks:")
        self.l_defaultEntity = QLabel()
        self.b_editDft = QToolButton()
        self.b_editDft.clicked.connect(self.editDefaultsClicked)
        self.b_editDft.setToolTip("Select for which tasks this preset will be used as a default...")
        iconPath = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "edit.png"
        )
        icon = self.core.media.getColoredIcon(iconPath)
        self.b_editDft.setIcon(icon)

        self.lo_dft = QHBoxLayout()
        self.lo_dft.addStretch()
        self.lo_dft.addWidget(self.l_default)
        self.lo_dft.addWidget(self.l_defaultEntity)
        self.lo_dft.addWidget(self.b_editDft)
        self.lo_dft.setContentsMargins(0, 0, 0, 0)

        self.lo_main = QHBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)

        self.lo_main.addWidget(self.l_name, 10)
        self.lo_main.addLayout(self.lo_dft, 20)

    @err_catcher(name=__name__)
    def editDefaultsClicked(self):
        self.dlg_defaults = DefaultTasksWindow(self)
        self.dlg_defaults.signalSaved.connect(self.setDftTasks)
        self.dlg_defaults.show()

    @err_catcher(name=__name__)
    def name(self):
        return self.l_name.text()

    @err_catcher(name=__name__)
    def setName(self, name):
        return self.l_name.setText(name or "")

    @err_catcher(name=__name__)
    def dftTasks(self):
        return self._dftTasks

    @err_catcher(name=__name__)
    def setDftTasks(self, tasks):
        newDftTasks = {
            "entities": ["*"],
            "departments": ["*"],
            "tasks": ["*"],
            "useExpression": False,
            "expression": "# set the variable \"result\" to True or False to decide when the default preset scenefile should get applied.\n# Example:\n#\n# context = core.getScenefileData(core.getCurrentFileName())\n# if context.get(\"department\") == \"rig\":\n#     result = True\n# else:\n#     result = False",
        }
        newDftTasks.update(tasks or {})

        self._dftTasks = newDftTasks
        entities = ", ".join(self._dftTasks["entities"])
        departments = ", ".join(self._dftTasks["departments"])
        tasks = ", ".join(self._dftTasks["tasks"])
        if len(self._dftTasks["entities"]) > 1:
            dataStr = "%s\n%s\n%s" % (entities, departments, tasks)
        else:
            dataStr = "%s - %s - %s" % (entities, departments, tasks)

        if dataStr == " -  - ":
            dataStr = "-"

        if self._dftTasks.get("useExpression") and self._dftTasks.get("expression"):
            dataStr += " + expression"

        self.l_defaultEntity.setText(dataStr)


class ProductTagItem(QWidget):

    removed = Signal(object)

    def __init__(self, core):
        super(ProductTagItem, self).__init__()
        self.core = core
        self.loadLayout()

    @err_catcher(name=__name__)
    def loadLayout(self):
        self.l_product = QLabel("Product:")
        self.e_product = QLineEdit()
        self.e_product.setPlaceholderText("Product name")
        self.e_product.setToolTip("Product name")
        
        self.l_tags = QLabel("Tags:")
        self.e_tags = QLineEdit()
        self.e_tags.setPlaceholderText("Comma separated tags")
        self.e_tags.setToolTip("Comma separated tags")
        
        self.b_remove = QToolButton()
        self.b_remove.clicked.connect(lambda: self.removed.emit(self))
        
        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "delete.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_remove.setIcon(icon)
        self.b_remove.setIconSize(QSize(20, 20))
        self.b_remove.setToolTip("Delete")
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_remove.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )
        
        self.lo_main = QHBoxLayout()
        self.lo_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.lo_main)
        
        self.lo_main.addWidget(self.l_product)
        self.lo_main.addWidget(self.e_product, 10)
        self.lo_main.addWidget(self.l_tags)
        self.lo_main.addWidget(self.e_tags, 10)
        self.lo_main.addWidget(self.b_remove)

    @err_catcher(name=__name__)
    def getProduct(self):
        return self.e_product.text().strip()

    @err_catcher(name=__name__)
    def setProduct(self, product):
        self.e_product.setText(product)

    @err_catcher(name=__name__)
    def getTags(self):
        return self.e_tags.text().strip()

    @err_catcher(name=__name__)
    def setTags(self, tags):
        self.e_tags.setText(tags)


class ProductTagsDlg(QDialog):
    def __init__(self, core, parent=None):
        super(ProductTagsDlg, self).__init__()
        self.parentDlg = parent
        self.core = core
        self.items = []
        self.setupUi()
        self.loadTags()

    @err_catcher(name=__name__)
    def setupUi(self):
        title = "Product Tags"

        self.setWindowTitle(title)
        self.core.parentWindow(self, parent=self.parentDlg)

        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        # Header label
        self.l_header = QLabel("Project wide product tags:")
        self.lo_main.addWidget(self.l_header)

        # Add button widget
        self.w_add = QWidget()
        self.b_add = QToolButton()
        self.lo_add = QHBoxLayout()
        self.w_add.setLayout(self.lo_add)
        self.lo_add.addStretch()
        self.lo_add.addWidget(self.b_add)

        path = os.path.join(
            self.core.prismRoot, "Scripts", "UserInterfacesPrism", "add.png"
        )
        icon = self.core.media.getColoredIcon(path)
        self.b_add.setIcon(icon)
        self.b_add.setIconSize(QSize(20, 20))
        self.b_add.setToolTip("Add Product Tag")
        self.b_add.clicked.connect(self.addItem)
        if self.core.appPlugin.pluginName != "Standalone":
            self.b_add.setStyleSheet(
                "QWidget{padding: 0; border-width: 0px;background-color: transparent} QWidget:hover{border-width: 1px; }"
            )

        # Items layout
        self.lo_items = QVBoxLayout()
        
        self.lo_main.addLayout(self.lo_items)
        self.lo_main.addWidget(self.w_add)
        self.lo_main.addStretch()

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Save", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)

        self.bb_main.clicked.connect(self.buttonClicked)
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def loadTags(self):
        tags = self.core.products.getProjectProductTags()
        self.clearItems()
        if tags:
            for product, tagList in tags.items():
                tagsStr = ", ".join(tagList) if isinstance(tagList, list) else tagList
                self.addItem(product=product, tags=tagsStr)

    @err_catcher(name=__name__)
    def addItem(self, product=None, tags=None):
        item = ProductTagItem(self.core)
        self.items.append(item)
        item.removed.connect(self.removeItem)
        
        if product:
            item.setProduct(product)
        
        if tags:
            item.setTags(tags)
        
        self.lo_items.addWidget(item)
        return item

    @err_catcher(name=__name__)
    def removeItem(self, item):
        self.items.remove(item)
        idx = self.lo_items.indexOf(item)
        if idx != -1:
            w = self.lo_items.takeAt(idx)
            if w.widget():
                w.widget().deleteLater()

    @err_catcher(name=__name__)
    def clearItems(self):
        for idx in reversed(range(self.lo_items.count())):
            item = self.lo_items.takeAt(idx)
            w = item.widget()
            if w:
                w.setVisible(False)
                w.deleteLater()
        
        self.items = []

    @err_catcher(name=__name__)
    def getTags(self):
        tagsDict = {}
        for item in self.items:
            product = item.getProduct()
            tags = item.getTags()
            if product:
                tagList = [t.strip() for t in tags.split(",") if t.strip()]
                tagsDict[product] = tagList
        return tagsDict

    @err_catcher(name=__name__)
    def buttonClicked(self, button):
        if button == "save" or button.text() == "Save":
            productTags = self.getTags()
            self.core.products.setProjectProductTags(productTags)

        self.close()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(600, 400)
