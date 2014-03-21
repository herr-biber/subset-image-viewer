#!/usr/bin/env python2
import fnmatch
import os
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
import argparse

class SubsetImageModel():
    def __init__(self, paths, split_token='-', suffix=''):
        self._paths = paths
        self._split_token = split_token
        self._suffix = suffix

        self._view = None
        self._active_subset = None

        # get subdirs of imagedir
        subdirs = self._paths

        # all subdirs should have the same number of tokens
        self._n_subsets = len(subdirs[0].split(self._split_token))
        assert all(len(s.split(self._split_token)) == self._n_subsets for s in subdirs), "All paths must have the same number of tokens"

        # add asterisks
        self.subsets = [set("*") for i in xrange(self._n_subsets)]
        for subdir in subdirs:
            tokens = subdir.split(self._split_token)
            for i, t in enumerate(tokens):
                self.subsets[i].add(t)

        # Mapping from changeable token index to index in complete range
        self._perm = []
        for i, subset in enumerate(self.subsets):
            if len(subset) != 2:  # * and one token
                self._perm.append(i)

        self.set_active_subset(['*'] * len(self._perm))
        self._update_filenames()

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
        tokens = ['*'] * self._n_subsets
        # but fill the given values
        for i, token in enumerate(self._active_subset):
            tokens[self._perm[i]] = token
        glob_pattern = self._split_token.join(tokens)
        self.filenames = sorted(fnmatch.filter(self._paths, glob_pattern))
        self.filenames = [fn + self._suffix for fn in self.filenames]

    def get_active_subset(self):
        return self._active_subset


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
        self.filename_changed()

    def get_subsets(self):
        return self._model.get_subsets()

    def get_filenames(self):
        return self._model.get_filenames()

    def filename_changed(self):
        filename = self._view.get_selected_filename()
        self._view.set_image(filename)


class SubsetImageView(QtGui.QWidget):
    def __init__(self, controller, parent=None):
        """
        @param controller:
        @type  controller: SubsetImageController
        """
        QtGui.QWidget.__init__(self, parent)
        controller.set_view(self)

        self.setWindowTitle('Subset image viewer')

        # Upper combo boxes
        hbox_upper = QtGui.QHBoxLayout()

        # Statically set combos
        subsets = controller.get_subsets()
        self.combos = []
        for subset in subsets:
            combo = QtGui.QComboBox()
            combo.addItems(subset)
            combo.currentIndexChanged.connect(controller.combos_changed)
            self.combos.append(combo)
            hbox_upper.addWidget(combo)

        # Image display
        self.image_widget = QtGui.QLabel()

        self.filenames = QtGui.QListWidget()
        self.filenames.addItems(controller.get_filenames())
        self.filenames.currentItemChanged.connect(controller.filename_changed)
        self.filenames.setFixedWidth(300)

        hbox_lower = QtGui.QHBoxLayout()
        hbox_lower.addWidget(self.image_widget, 1)  # scaled
        hbox_lower.addWidget(self.filenames)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox_upper)
        vbox.addLayout(hbox_lower)
        self.setLayout(vbox)

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
            pixmap = QtGui.QPixmap(filename)
            self.image_widget.setPixmap(pixmap)
        self.resizeEvent(None)

    def set_filenames(self, filenames):
        self.filenames.clear()
        self.filenames.addItems(filenames)

    def resizeEvent(self, QResizeEvent):
        # Arbitrary scaling, but no aspect ratio
        # self.image_widget.setScaledContents(True)

        # TODO window can not be rescaled to smaller size, since pixmap is set to fixed width and height
        pixmap = self.image_widget.pixmap()
        if pixmap and not pixmap.isNull():
            self.image_widget.setPixmap(pixmap.scaled(self.image_widget.size(), Qt.KeepAspectRatio))

def main():

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--suffix', '-s', default='', help='Suffix which is appended to all paths')
    parser.add_argument('--delimiter', '-d', default='-', help='Delimiter for splitting paths')
    parser.add_argument('--ignore-missing', '-i', action='store_true')
    parser.add_argument('--paths', '-p', nargs='+', help='Paths')

    args = parser.parse_args()

    paths = []
    if args.ignore_missing:
        for path in args.paths:
            file = path + args.suffix
            if not os.path.exists(file):
                sys.stderr.write("Ignoring missing file: %s\n" % file)
            else:
                paths.append(path)
    else:
        paths = args.paths

    app = QtGui.QApplication(sys.argv)
    sim = SubsetImageModel(paths=paths, split_token=args.delimiter, suffix=args.suffix)
    sic = SubsetImageController()
    sic.set_model(sim)
    siv = SubsetImageView(sic)
    siv.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
