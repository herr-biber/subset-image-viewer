#!/usr/bin/env python
from __future__ import print_function
import fnmatch
import os
import re
import sys
import argparse

import numpy as np
from PIL import Image

try:
    from PySide import QtGui
    from PySide.QtCore import Qt, QSize
except:
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt, QSize

from patternreplacer import PatternReplacer


class SubsetImageModel():
    def __init__(self, paths, split_tokens='-', suffix=''):
        self._paths = paths
        self._split_token = split_tokens
        self._suffix = suffix

        self._view = None
        self._active_subset = None
        self._glob_pattern = None
        self.filenames = None

        # get subdirs of imagedir
        subdirs = self._paths

        # use first path as pattern
        print("Creating pattern")
        self.pr = PatternReplacer(subdirs[0], split_tokens)
        self._n_subsets = self.pr.get_n_tokens()

        # all subdirs should have the same number of tokens
        print("Verifying filenames")
        assert all(self.pr.verify(s) for s in subdirs), "All paths must have the same number of tokens"

        # add asterisks
        self.subsets = [set("*") for i in range(self._n_subsets)]
        for subdir in subdirs:
            tokens = re.split("|".join(re.escape(t) for t in split_tokens), subdir)
            tokens = [t for t in tokens if t]  # remove empty ones
            assert len(tokens) == self._n_subsets
            for i, t in enumerate(tokens):
                self.subsets[i].add(t)

        self.default_subsets = ["*"] * self._n_subsets

        # Mapping from changeable token index to index in complete range
        self._perm = []
        for i, subset in enumerate(self.subsets):
            if len(subset) != 2:  # * and one token
                self._perm.append(i)
            else:
                # fix tokens which are unique. No need to glob them
                assert '*' in subset
                self.default_subsets[i] = (subset - set('*')).pop()
        self.set_active_subset(['*'] * len(self._perm))

    def _changeable_to_total(self, changeable):
        # fill total pattern with changeable using perm
        pass

    def __total_to_changeable(self, total):
        # use only the ones mentioned in perm
        pass

    def get_subsets(self):
        # return only changeable subsets
        return [sorted(self.subsets[i]) for i in self._perm]

    def get_filenames(self):
        return self.filenames

    def set_active_subset(self, active_subset):
        self._active_subset = active_subset
        self._update_filenames()

    def _update_filenames(self):
        # glob everything
        tokens = list(self.default_subsets)
        # but fill the given values
        for i, token in enumerate(self._active_subset):
            tokens[self._perm[i]] = token

        self._glob_pattern = self.pr.replace(tokens)
        self.filenames = sorted(fnmatch.filter(self._paths, self._glob_pattern))
        self.filenames = [fn + self._suffix for fn in self.filenames]

    def get_active_subset(self):
        return self._active_subset

    def get_glob_pattern(self):
        return self._glob_pattern


class SubsetImageController():
    def __init__(self):
        self._model = None
        self._view = None

    def set_view(self, view):
        """
        @type view: SubsetImageView
        """
        self._view = view

    def set_model(self, model):
        """
        @type model: SubsetImageModel
        """
        self._model = model

    def combos_changed(self):
        self._model.set_active_subset(self._view.get_selected_subset())
        self._view.set_filenames(self._model.get_filenames())
        self._view.set_statusbar(self.get_glob_pattern())
        self.filename_changed()

    def get_subsets(self):
        return self._model.get_subsets()

    def get_filenames(self):
        return self._model.get_filenames()

    def filename_changed(self):
        filename = self._view.get_selected_filename()
        self._view.set_image(filename)

    def get_glob_pattern(self):
        return self._model.get_glob_pattern()


class ListWidget(QtGui.QListWidget):
    def sizeHint(self):
        s = QSize()
        s.setHeight(super(ListWidget, self).sizeHint().height())
        # hint to max text length
        # width from scrollbar is too big? just use half of it.
        s.setWidth(self.sizeHintForColumn(0) + self.verticalScrollBar().width() / 2)
        return s


class SubsetImageView(QtGui.QWidget):
    def __init__(self, controller, parent=None):
        """
        @param controller:
        @type  controller: SubsetImageController
        """
        QtGui.QWidget.__init__(self, parent)
        self._controller = controller
        controller.set_view(self)

        self.setWindowTitle('Subset image viewer')

        # Upper combo boxes
        hbox_upper = QtGui.QHBoxLayout()

        # Statically set combos
        subsets = controller.get_subsets()
        if len(subsets) == 1:
            subsets = []

        self.combos = []
        for subset in subsets:
            combo = QtGui.QComboBox()
            combo.addItems(subset)
            combo.currentIndexChanged.connect(self._combos_changed)
            self.combos.append(combo)
            hbox_upper.addWidget(combo, 1)

        self.anti_alias = QtGui.QCheckBox()
        self.anti_alias.setText("AA")
        self.anti_alias.setToolTip("anti-aliasing (F1)")
        self.anti_alias.setFixedSize(self.anti_alias.sizeHint())
        self.anti_alias.stateChanged.connect(self.resizeEvent)
        hbox_upper.addWidget(self.anti_alias, 0, Qt.AlignRight)

        # Image display
        self.image = QtGui.QPixmap()
        self.image_widget = QtGui.QLabel()
        # allow widget to decreased in size
        self.image_widget.setMinimumSize(1, 1)

        # filename list
        self.filenames = ListWidget()
        self.filenames.currentItemChanged.connect(controller.filename_changed)
        self.filenames.updateGeometry()

        # open collapsed
        if len(controller.get_filenames()) > 5000:
            print("Found more than 5000 images. Preselecting subsets for faster loading.")
            for combo in self.combos:
                combo.setCurrentIndex(1)

        # trigger loading of filename list
        self._combos_changed()

        hbox_lower = QtGui.QSplitter(Qt.Horizontal)
        hbox_lower.splitterMoved.connect(self.resizeEvent)
        hbox_lower.addWidget(self.image_widget)
        hbox_lower.addWidget(self.filenames)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox_upper)
        vbox.addWidget(hbox_lower)
        self.setLayout(vbox)

        # select first file on startup
        if self.filenames.count() > 0:
            self.filenames.setCurrentRow(0)
            controller.filename_changed()

            # initial focus on list
            self.filenames.setFocus()

    def keyPressEvent(self, key_event):
        # anti alias keyboard shortcut
        if key_event.key() == Qt.Key_F1:
            self.anti_alias.nextCheckState()

        # copy current filename to clipboard
        if key_event.key() == Qt.Key_F2:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(self.get_selected_filename())

        if key_event.key() == Qt.Key_F3:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(self._controller.get_glob_pattern())

    def get_selected_subset(self):
        selected_combos = []
        for c in self.combos:
            assert isinstance(c, QtGui.QComboBox)
            selected_combos.append(str(c.currentText()))
        return selected_combos

    def get_selected_filename(self):
        current_item = self.filenames.currentItem()
        if current_item is not None:
            return current_item.text()
        else:
            return None

    def set_image(self, filename):

        if not filename:
            return
        if not os.path.exists(filename):
            self.image_widget.setText("File not found: \n" + filename)
        else:
            is_monochrome_16_tiff = False
            image_reader = QtGui.QImageReader(filename)
            
            # use pil to decide for 16 bit tiff
            i = Image.open(filename)
            if(image_reader.format() == 'tiff'):
                if i.mode == 'I;16':
                    is_monochrome_16_tiff = True
                
            # open 16 bit monochrome tiff using PIL and make drawable 8 bit out of it
            if is_monochrome_16_tiff:
         
                # np array from pil image
                # TODO maybe use pil to get rid of numpy dependency
                image = np.array(i.getdata()).reshape(i.size[0], i.size[1])
                
                # # use leftmost 8 bit starting from first 1
                shift = int(np.ceil(np.log2(np.max(image)))) - 8  
                shift = max(shift, 0)  # use rightmost 8 bit, if max is smaller than 255
                image >>= shift
                
                # assemble QImage data structure
                image = (255 << 24 | image << 16 | image << 8 | image)  # ARGB from grayscale
                image = image.astype(np.uint32)
                image = QtGui.QImage(image.ravel(), image.shape[0], image.shape[1], QtGui.QImage.Format_RGB32).copy()
            else:
                image = image_reader.read()
            
            self.image = QtGui.QPixmap(image)
            self.image_widget.setPixmap(self.image)
        self.resizeEvent()

    def set_filenames(self, filenames):
        self.filenames.clear()
        self.filenames.addItems(filenames)
        self.filenames.setMaximumWidth(self.filenames.sizeHint().width())


    def resizeEvent(self, resize_event=None):
        if self.image and not self.image.isNull():
            transformation_mode = Qt.SmoothTransformation if self.anti_alias.checkState() else Qt.FastTransformation
            self.image_widget.setPixmap(
                self.image.scaled(self.image_widget.size(), Qt.KeepAspectRatio, transformation_mode))

    def set_statusbar(self, message, time=10000):
        self.parent().statusBar().showMessage(message, time)

    def _combos_changed(self):
        current_item_text = self.filenames.currentItem().text() if self.filenames.currentItem() is not None else None
        self._controller.combos_changed()

        item_in_updated_list = self.filenames.findItems(current_item_text, Qt.MatchExactly)\
            if current_item_text is not None else None
        if item_in_updated_list:
            # use previously selected item in new list
            self.filenames.setCurrentItem(item_in_updated_list[0])
        else:
            # otherwise select first item
            self.filenames.setCurrentRow(0)

def main():
    parser = argparse.ArgumentParser(description='Subset image viewer.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--suffix', '-s', default='', help='suffix which is appended to all paths')
    parser.add_argument('--delimiters', '-d', default='@', help='delimiters for splitting paths')
    parser.add_argument('--ignore-missing', '-i', action='store_true', help='ignore missing paths')
    parser.add_argument('paths', nargs='+', help='image file names. Use - to read file names from stdin')

    args = parser.parse_args()

    if args.paths == ['-']:
        print("Reading file names from stdin")
        paths = [l.strip() for l in sys.stdin.readlines()]
    else:
        paths = args.paths

    if args.ignore_missing:
        valid_paths = []
        for path in paths:
            filename = path + args.suffix
            if not os.path.exists(filename):
                sys.stderr.write("Ignoring missing file: %s\n" % filename)
            elif not os.path.isfile(filename):
                sys.stderr.write("Ignoring directory: %s\n" % filename)
            else:
                valid_paths.append(path)
        paths = valid_paths

    print("%d files loaded" % len(paths))

    app = QtGui.QApplication(sys.argv)
    sim = SubsetImageModel(paths=paths, split_tokens=args.delimiters, suffix=args.suffix)
    sic = SubsetImageController()
    sic.set_model(sim)
    main_window = QtGui.QMainWindow()
    siv = SubsetImageView(sic, main_window)
    main_window.setWindowTitle("siv - Subset Image Viewer")
    main_window.setCentralWidget(siv)
    print("Loading GUI")
    main_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
