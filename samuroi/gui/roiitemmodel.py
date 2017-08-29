from PyQt5 import QtCore

from PyQt5.QtCore import QVariant, QObject, pyqtSignal
from PyQt5.QtCore import QAbstractItemModel, QModelIndex


class TreeItem(object):
    def __init__(self, model, parent=None):
        super(TreeItem, self).__init__()
        self.__children = []
        self.__parent = parent
        self.__model = model

    @property
    def model(self):
        """The treemodel where this node is attached."""
        return self.__model

    @property
    def mask(self):
        """ return the mask asociated with the item, or None if there is no mask."""
        return None

    @property
    def name(self):
        """ the name of the group. if there is a mask attached return mask name, otherwise group name."""
        raise NotImplementedError("implement in derived class")

    def child(self, row):
        return self.children[row]

    def find(self, mask):
        """find the treeitem of the given mask"""
        raise NotImplementedError("implement in derived class")

    def add(self, children):
        children = children if hasattr(children, '__iter__') else [children]
        i = len(self)
        self.model.beginInsertRows(self.index, len(self), len(self) + len(children) - 1)
        self.__children.extend(children)
        self.model.endInsertRows()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())
        return i

    def remove(self, child=None, slice=None):
        if child is not None:
            childi = self.row(child)
            self.model.beginRemoveRows(self.index, childi, childi)
            self.__children.remove(child)
            self.model.endRemoveRows()
        elif slice is not None:
            indices = slice.indices(len(self))
            self.model.beginRemoveRows(self.index, indices[0], indices[0] + indices[1] - indices[0] - 1)
            del self.__children[slice]
            self.model.endRemoveRows()

    @property
    def index(self):
        """Get the model index of this tree item"""
        # root does have default model index
        if self.__parent is None:
            return QModelIndex()
        else:
            return self.model.index(self.parent.row(self), 0, self.parent.index)

    @property
    def parent(self):
        return self.__parent

    @property
    def children(self):
        return self.__children

    def row(self, child):
        return self.children.index(child)

    def __len__(self):
        return len(self.__children)


class RootItem(TreeItem):
    def __init__(self, model):
        TreeItem.__init__(self, model=model)

        # keep track of type to child index mapping
        self.type2group = {}  # todo rename to better name

    def add(self, mask):
        """return the added item"""
        # check if we have a group for the type of the mask
        if type(mask) not in self.type2group:
            group = self.type2group[type(mask)] = RoiGroupItem(model=self.model, parent=self,
                                                               name=str(type(mask).__name__))
            TreeItem.add(self, group)
        # call on_added on child item
        index = self.row(self.type2group[type(mask)])
        self.child(index).add(mask)

    def find(self, mask):
        """Return the tree node that holds given mask."""
        # because the mask could be a child mask of any type we need to search all groups
        for child in self.children:
            node = child.find(mask)
            if node is not None:
                return node
        return None

    @TreeItem.mask.getter
    def mask(self):
        return None

    @TreeItem.name.getter
    def name(self):
        return "Root"

    def remove(self, mask):
        # remove the mask from the respective child item
        index = self.row(self.type2group[type(mask)])
        self.child(index).remove(mask)

        # check if there are still other items within the group
        if len(self.child(index)) == 0:
            TreeItem.remove(self, self.child(index))
            del self.type2group[type(mask)]


class RoiGroupItem(TreeItem):
    def __init__(self, model, parent, name):
        TreeItem.__init__(self, model=model, parent=parent)
        self.__name = name

    @TreeItem.name.getter
    def name(self):
        return self.__name

    def find(self, mask):
        for child in self.children:
            node = child.find(mask)
            if node is not None:
                return node
        return None

    def add(self, mask):
        child = RoiItem(model=self.model, parent=self)
        TreeItem.add(self, child)
        # set mask after insertion into tree, because setting the mask may require adding sub masks.
        # adding sub masks required the parent item to be in the tree already
        child.mask = mask

    def remove(self, mask):
        for node in self.children:
            if node.mask is mask:
                return TreeItem.remove(self, node)
        # mask needs to be one of the direct child nodes
        assert (False)

    def __repr__(self):
        return self.__name

    @TreeItem.mask.getter
    def mask(self):
        return None


class RoiItem(TreeItem):
    def __init__(self, parent, model):
        super(RoiItem, self).__init__(parent=parent, model=model)
        self.__mask = None

    @property
    def mask(self):
        return self.__mask

    @mask.setter
    def mask(self, m):
        self.__mask = m
        if hasattr(self.mask, "children"):
            TreeItem.add(self, [RoiItem(parent=self, model=self.model) for child in self.mask.children])
            for item, mask in zip(self.children, self.mask.children):
                item.mask = mask
        if hasattr(self.mask, "changed"):
            self.mask.changed.append(self.on_mask_changed)

    def find(self, mask):
        if mask is self.__mask:
            return self
        for child in self.children:
            node = child.find(mask)
            if node is not None:
                return node
        return None

    @TreeItem.name.getter
    def name(self):
        return self.__mask.name

    def on_mask_changed(self, mask):
        assert (mask is self.mask)

        # remove all children
        TreeItem.remove(self, slice=slice(None))

        # add all children
        if (hasattr(self.mask, "children")):
            TreeItem.add(self, [RoiItem(parent=self, model=self.model) for child in self.mask.children])
            for item, mask in zip(self.children, self.mask.children):
                item.mask = mask

    def __repr__(self):
        if hasattr(self.mask, "events"):
            if len(self.mask.events.indices) > 0:
                return self.mask.name + "*"
        return self.mask.name


class RoiTreeModel(QAbstractItemModel):
    mask_added = pyqtSignal(object)
    mask_removed = pyqtSignal(object)

    def __init__(self, rois, parent=None):
        super(RoiTreeModel, self).__init__(parent)
        self.root = RootItem(model=self)
        self.masks = rois
        # notify the data tree about changes, to do this, proxy the events into the qt event loop
        self.masks.added.append(self.mask_added.emit)
        self.masks.preremove.append(self.mask_removed.emit)
        # now connect to the own signals
        self.mask_added.connect(self.root.add)
        self.mask_removed.connect(self.root.remove)

        # self.mask2roitreeitem = {}

        """ Keep track of all items in the hierarchy and provide easy mapping from mask to the treeitems of the rois"""

    def flags(self, index):
        """Determines whether a field is editable, selectable checkable etc"""
        if index.isValid():
            item = index.internalPointer()
            if item.mask is not None:
                # allow to change the name of a mask
                return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        # all other fields can't be edited
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def find(self, mask):
        """ find the tree index of the given mask"""
        return self.root.find(mask).index

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        """Sets the role data for the item at index to value."""
        if not index.isValid():
            return False
        if role == QtCore.Qt.EditRole:
            name = str(value.toPyObject())
            print name
            index.internalPointer().mask.name = name
            self.dataChanged.emit(index, index)
            return True

        return False

    def columnCount(self, parent):
        """Returns the number of columns for the children of the given parent index.
        Here the number of columns will always be one."""
        return 1

    def data(self, index, role):
        """Returns the data stored under the given role for the item referred to by the index."""
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = index.internalPointer()

        return QVariant(repr(item))

    def index(self, row, column, parent):
        """
        Returns the index of the item in the model specified by the given row,
        column and parent index.
        Calls base class createIndex() to generate model indexes that other
        components can use to refer to items in this model.
        """
        # convert parent index to parent item
        item = parent.internalPointer() if parent.isValid() else self.root
        # get the respective child from the parent item
        child = item.child(row)

        return self.createIndex(row, column, child)

    def parent(self, index):
        """Returns the parent of the model item with the given index. If the item has
        no parent, an invalid QModelIndex is returned."""
        item = index.internalPointer() if index.isValid() else self.root

        if item is self.root:
            return QModelIndex()
        return item.parent.index

    def rowCount(self, parent):
        """Returns the number of rows under the given parent index. When the parent is valid
        it means that rowCount is returning the number of children of parent."""
        item = parent.internalPointer() if parent.isValid() else self.root

        return len(item)
