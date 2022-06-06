import os
import PyPDF2
from tabulate import tabulate


class Node:
    nodes = []
    init_path = None
    sting_tree_indent_char = '-'
    sting_tree_indent_char_repeat = 1
    
    def __init__(self, path, nested_level=0, node_file_path=None):
        self.path = path
        self.nested_level = nested_level
        self.node_file_path = node_file_path
        self.is_file = os.path.isfile(self.path)
        self.parent_index = self.get_parent_index()
        self.bookmark_page = None
        self.title = self.title_from_path()
        self.__class__.nodes.append(self)
        self.assign_file_path()
    
    def title_from_path(self):
        if self.is_file:
            return os.path.splitext(os.path.basename(self.path))[0]
        return os.path.basename(self.path)
        
    def get_parent_index(self):
        for i, node in list(enumerate(self.__class__.nodes))[::-1]:
            if node.nested_level < self.nested_level:
                return i
        return -1
    
    def assign_file_path(self):
        if self.is_file:
            for node in self.__class__.nodes[:-1][::-1]:
                if not node.node_file_path:
                    node.node_file_path = self.node_file_path
                else:
                    break
                   
    @classmethod
    def make_nodes(cls):
        times = cls.sting_tree_indent_char_repeat
        cls.nodes.clear()
        for root, dirs, files in os.walk(cls.init_path):
            level = root.replace(cls.init_path, '').count(os.sep)
            Node(root, times * level)
            for f in [os.path.join(root, f) for f in files]:
                if f.endswith('.pdf'):
                    Node(f, times * (level + 1), f)
                    
    @classmethod
    def make_string_tree(cls):
        data = []
        for i, node in enumerate(cls.nodes):
            idx = i
            is_file = 1 * node.is_file
            parent_idx = node.parent_index
            indent = node.nested_level * cls.sting_tree_indent_char
            title = f"{indent}{node.title}"
            item = [idx, is_file, parent_idx, title]
            data.append(item)
        return tabulate(data, headers=['Idx', 'IsFile', 'ParentIdx', 'Tree'], tablefmt='fancy_grid')

                    
class PdfMerger:
    
    def __init__(
        self,
        init_path,
        sting_tree_indent_char='-',
        sting_tree_indent_char_repeat=2,
        watermark_file_path=None,
    ):
        '''init_path is absolute and it is at the top of the tree'''
        self.init_path = str(init_path)
        self.watermark_file_path = watermark_file_path
        self.node = Node
        ###################
        self.node.init_path = self.init_path
        self.node.sting_tree_indent_char = sting_tree_indent_char
        self.node.sting_tree_indent_char_repeat = sting_tree_indent_char_repeat
        self.node.make_nodes()
        ###################
        self.nodes = self.node.nodes
        self.string_tree = self.node.make_string_tree()
        # Track opened files to close them after merging
        self.files_to_close = []
        
    def add_watermark(self, page_obj):
        if self.watermark_file_path:
            # https://indianpythonista.wordpress.com/2017/01/10/working-with-pdf-files-in-python/
            watermark_file_obj = open(self.watermark_file_path, 'rb')
            pdfReader = PyPDF2.PdfFileReader(watermark_file_obj) 
            watermark_page = pdfReader.getPage(0)
            watermark_page.mergePage(page_obj)
            self.files_to_close.append(watermark_file_obj)
            return watermark_page
        return page_obj
    
    def merge_files(self):
        current_bookmark_page = 0
        bookmark_objects = []
        file_writer = PyPDF2.PdfFileWriter()
        # Open Bookmarks panel when file is open
        file_writer.setPageMode("/UseOutlines")
        
        # Merge files
        for i, node in enumerate(self.nodes):
            node.bookmark_page = current_bookmark_page
            if node.is_file:
                input_file = open(node.node_file_path, 'rb')
                file_reader = PyPDF2.PdfFileReader(input_file)
                file_pages = file_reader.numPages
                for page_num in range(file_pages):
                    watermarked_page = self.add_watermark(file_reader.getPage(page_num))
                    file_writer.addPage(watermarked_page)
                self.files_to_close.append(input_file)
                current_bookmark_page += file_pages
        
        # Add Bookmarks
        # https://pypdf2.readthedocs.io/en/latest/modules/PdfWriter.html?highlight=addbookmark#PyPDF2.PdfWriter.add_bookmark
        # https://pypdf2.readthedocs.io/en/latest/modules/PdfWriter.html?highlight=addLink#PyPDF2.PdfWriter.add_link
        for node in self.nodes:
            parent = None if node.parent_index < 0 else bookmark_objects[node.parent_index]
            bookmark = file_writer.add_bookmark(node.title,         # title
                                                node.bookmark_page, # pagenum
                                                parent,             # parent
                                                None,               # color
                                                not node.is_file,   # bold
                                                False,              # italic
                                               )
            bookmark_objects.append(bookmark)
        
        output_filename = os.path.join(os.path.abspath(os.path.join(self.init_path, os.pardir)), 'output.pdf')
        with open(output_filename, 'wb') as f:
            file_writer.write(f)
            
        [f.close() for f in self.files_to_close]
        self.files_to_close.clear()