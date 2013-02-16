# coding= utf-8

from Tkinter import *
from ttk import *
from tkFileDialog import askopenfilename
from re import findall, search
from os import path, system
from pickle import load, dump
from subprocess import Popen, PIPE
from operator import itemgetter
import codecs

PREFERENCES_FILE = path.expanduser('~/Library/Preferences/org.python.LaTeXStructure.preferences')

SECTIONKINDS = {'title': 0, 'begin{document}': 1, 'part': 2, 'chapter': 3, 'chapter*': 3, 'section': 4, 'section*': 4, 'subsection': 5, 'subsection*': 5, 'subsubsection': 6, 'subsubsection*': 6, 'paragraph': 7, 'subparagraph': 8}
SECTIONKINDSPRINT = {'title': 'TITLE', 'part': 'Part ', 'chapter': 'Chap. ', 'chapter*': 'Chap. ', 'section': u'§', 'section*': '', 'subsection': u'§', 'subsection*': '', 'subsubsection': u'§', 'subsubsection*': '', 'paragraph': '', 'subparagraph': ''}
COMBOBOXENTRIES = ['Table of Contents', 'Footnotes', 'Citations', 'Labels and References', 'To Do Items', 'Figures', 'Index Entries', 'Tables']

ROOT = None
WINDOWLIST = []

class DocumentStructure:

	def __init__(self, master, filename):
		self.master = master
		self.filename = filename
		self.window = Toplevel(self.master)
		self.window.minsize(175, 200)
		self.window.geometry(get_window_geometry_preferences(self.filename))
		self.frame = Frame(self.window, padding = (0, 3, 0, 6))
		self.combobox = Combobox(self.frame, state = 'readonly')
		self.combobox['values'] = COMBOBOXENTRIES
		self.combobox.current(0)
		self.combobox.bind('<<ComboboxSelected>>', self.combobox_select)

		self.search_field_text = StringVar()
		self.searchbox = Entry(self.frame, textvariable = self.search_field_text, takefocus = 1)

		self.scrollbarv = Scrollbar(self.frame, orient = 'vertical')
		self.scrollbarh = Scrollbar(self.frame, orient = 'horizontal')
		self.treelist = Treeview(self.frame, height = 49, yscrollcommand = self.scrollbarv.set, xscrollcommand = self.scrollbarh.set, takefocus = 1, selectmode = 'browse')
		self.scrollbarv.config(command = self.treelist.yview)
		self.scrollbarh.config(command = self.treelist.xview)
		self.treelist.tag_configure('greyed_out', foreground = 'grey')
		self.treelist.tag_configure('found', foreground = 'black')
		self.treelist.tag_configure('empty', foreground = 'red')

		self.sorted_status = IntVar()
		self.sort_button = Checkbutton(self.frame, text = 'Sorted', variable = self.sorted_status, command = self.sorted_pushed)
		self.sorted_status.set(1)
		self.refresh_button = Button(self.frame, text = 'Refresh', command = self.refresh_pushed, underline = 0, takefocus = 0)

		self.frame.grid(row = 0, column = 0, sticky = (N, S, E, W))
		self.combobox.grid(row = 0, columnspan = 3, sticky = (W, E))
		self.searchbox.grid(row = 1, columnspan = 3, sticky = (W, E))
		self.treelist.grid(row = 2, columnspan = 2, sticky = (W, E, N, S))
		self.treelist.column('#0', minwidth = 750)
		self.scrollbarv.grid(row = 2, column = 2, sticky = (N, S))
		self.scrollbarh.grid(row = 3, columnspan = 2, sticky = (W, E))
		self.sort_button.grid(row = 4, column = 0)
		self.refresh_button.grid(row = 4, column = 1)

		self.window.columnconfigure(0, weight = 1)
		self.window.rowconfigure(0, weight = 1)
		self.frame.columnconfigure(0, weight = 1)
		self.frame.columnconfigure(1, weight = 1)
		self.frame.rowconfigure(2, weight = 1)

		self.treelist.bind('<Double-Button-1>', self.item_selected)
		self.treelist.bind('<Return>', self.item_selected)
		self.treelist.bind('<Command-Return>', self.item_select_and_go)
		self.search_field_text.trace('w', self.search_entered)
		self.window.bind('<Command-KeyPress-1>', self.combobox_select)
		self.window.bind('<Command-KeyPress-2>', self.combobox_select)
		self.window.bind('<Command-KeyPress-3>', self.combobox_select)
		self.window.bind('<Command-KeyPress-4>', self.combobox_select)
		self.window.bind('<Command-KeyPress-5>', self.combobox_select)
		self.window.bind('<Command-KeyPress-6>', self.combobox_select)
		self.window.bind('<Command-KeyPress-7>', self.combobox_select)
		self.window.bind('<Command-KeyPress-8>', self.combobox_select)
		self.window.bind('<Command-KeyPress-r>', self.refresh)
		self.window.bind('<Command-KeyPress-s>', self.sorted_select)
		self.window.bind('<Command-KeyPress-f>', self.focus_search_box)
		self.window.bind('<Command-KeyPress-w>', self.graceful_close)
		self.master.bind_all('<Command-KeyPress-o>', open_new_document)
		self.master.bind_all('<Command-KeyPress-t>', open_TeXShop_document)
		self.master.bind_all('<Command-KeyPress-q>', graceful_quit)


		self.menubar = Menu(self.window)
		self.filemenu = Menu(self.menubar, tearoff = 0)
		self.filemenu.add_command(label = 'Open...', command = open_new_document, accelerator = 'Command+o')
		self.filemenu.add_command(label = 'Open from TeXShop', command = open_TeXShop_document, accelerator = 'Command+t')
		self.filemenu.add_separator()
		self.filemenu.add_command(label = 'Refresh', command = self.refresh, accelerator = 'Command+r')
		self.filemenu.add_separator()
		self.filemenu.add_command(label = 'Close Document', command = self.graceful_close, accelerator = 'Command+w')

		self.editmenu = Menu(self.menubar, tearoff = 0)
		self.editmenu.add_command(label = 'Find', command = self.focus_search_box, accelerator = 'Command+f')
		self.editmenu.add_command(label = 'Sorted', command = self.sorted_select, accelerator = 'Command+s')

		self.viewmenu = Menu(self.menubar, tearoff = 0)
		self.viewmenu.add_command(accelerator = 'Command+1', label = 'Table of Contents')
		self.viewmenu.add_command(accelerator = 'Command+2', label = 'Footnotes')
		self.viewmenu.add_command(accelerator = 'Command+3', label = 'Citations')
		self.viewmenu.add_command(accelerator = 'Command+4', label = 'Labels and Cross References')
		self.viewmenu.add_command(accelerator = 'Command+5', label = 'To Do Items')
		self.viewmenu.add_command(accelerator = 'Command+6', label = 'Figures')
		self.viewmenu.add_command(accelerator = 'Command+7', label = 'Index Entries')
		self.viewmenu.add_command(accelerator = 'Command+8', label = 'Tables')

		self.helpmenu = Menu(self.menubar, tearoff = 0)

		self.menubar.add_cascade(label = 'File', menu = self.filemenu)
		self.menubar.add_cascade(label = 'Edit', menu = self.editmenu)
		self.menubar.add_cascade(label = 'View', menu = self.viewmenu)
		self.menubar.add_cascade(label = 'Help', menu = self.helpmenu)
		self.window.config(menu = self.menubar)

		self.last_branch_selected = '0'

		self.refresh()

	def refresh(self, *args):
		self.get_file(self.filename)
		if len(self.document) > 0:
			self.populate_treelist()
			self.window.wm_title(self.filename[self.filename.rfind('/') + 1:])	# Set window title
		else:
			self.window.wm_title('** No file open in TeXShop **')
			x = self.treelist.get_children()
			for item in x: self.treelist.delete(item)
		self.search_entered()
		try:
			self.get_last_tree_selected()
			self.treelist.selection_set(self.last_branch_selected)	# Select this item
			self.treelist.focus_set()		# Set focus on the self.treelist
			self.treelist.focus(self.last_branch_selected)			# Set keyboard focus on this item
		except TclError: pass			# Ignore error if self.treelist is empty.

	def get_file(self, filename):
		try:
			with codecs.open(filename, 'r', 'utf-8') as file:
				self.document = file.read()
		except IOError:
			self.treelist.bell()
			self.document = ''
		self.begin_document_position = self.document.find('\\begin{document}') + 16

	def populate_treelist(self, *args):
		'''
			Populates self.treelist with elements from self.TOC corresponding to the
			self.combobox option.
		'''
		option = COMBOBOXENTRIES.index(self.combobox.get())
		if option == 0:
			self.sort_button.configure(state = 'disabled')
			self.toc_to_treelist()
		elif option == 1:
			self.sort_button.configure(state = 'disabled')
			self.footnotes_to_treelist()
		elif option == 2:
			self.sort_button.configure(state = 'normal')
			self.cites_to_treelist()
		elif option == 3:
			self.sort_button.configure(state = 'normal')
			self.crossrefs_to_treelist()
		elif option == 4:
			self.sort_button.configure(state = 'disabled')
			self.todos_to_treelist()
		elif option == 5:
			self.sort_button.configure(state = 'disabled')
			self.figures_to_treelist()
		elif option == 6:
			self.sort_button.configure(state = 'normal')
			self.index_to_treelist()
		elif option == 7:
			self.sort_button.configure(state = 'disabled')
			self.tables_to_treelist()
		else: print 'ERROR! Combobox out of range.'
		if len(self.treelist.get_children()) == 0:
			self.treelist.insert('', 'end', '0', text = '(Empty)', tags = 'empty')
			self.last_branch_selected = '0'
		self.treelist.selection_set(self.last_branch_selected)
		self.treelist.focus(self.last_branch_selected)	# Set keyboard focus on this item

	def toc_to_treelist(self):
		self.get_TOC()
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		if len(self.TOC) > 0:
			if SECTIONKINDSPRINT[self.TOC[0]['kind']] == '': text = self.TOC[0]['title']
			elif SECTIONKINDSPRINT[self.TOC[0]['kind']] == 'TITLE': text = "TITLE: " + self.TOC[0]['title']
			else: text = SECTIONKINDSPRINT[self.TOC[0]['kind']] + self.TOC[0]['number'] + ': ' + self.TOC[0]['title']
			self.treelist.insert('', 'end', '0', text = text, open = True)
			treenum = 1
			for item in range(1, len(self.TOC)):
				parent = ''
				for earlier in range(item - 1, -1, -1):
					if SECTIONKINDS[self.TOC[item]['kind']] > SECTIONKINDS[self.TOC[earlier]['kind']]:
						parent = unicode(earlier)
						break
				if SECTIONKINDSPRINT[self.TOC[item]['kind']] == '': text = self.TOC[item]['title']
				else: text = SECTIONKINDSPRINT[self.TOC[item]['kind']] + self.TOC[item]['number'] + ': ' + self.TOC[item]['title']
				self.treelist.insert(parent, 'end', unicode(treenum), text = text, open = True)
				treenum += 1

	def get_TOC(self):
		self.TOC = []
		titleposition = self.document.find('\\title{')
		if titleposition > -1:
			title = get_brace_text(self.document[titleposition:])
			self.TOC.append(dict(kind = 'title', title = title, number = ''))
		founditems = findall('\\\\(part\\*?|chapter\\*?|section\\*?|subsection\\*?|subsubsection\\*?|paragraph|subparagraph)(\\[.*?\\])?{(.*)}', self.document[self.begin_document_position:])
		for item in founditems:
			kind, shorttitle, title = item
			if '\\label{' in title: title = title[:title.find('\\label{')].rstrip('}')
			if '\\index{' in title: title = title[:title.find('\\index{')].rstrip('}')
			self.TOC.append(dict(kind = kind, title = title, shorttitle = shorttitle))
		index = [0 for i in range(len(SECTIONKINDS))]
		for i in range(len(self.TOC)):
			if i > 0: previousdepth = SECTIONKINDS[self.TOC[i-1]['kind']]
			else: previousdepth = 0
			currentdepth = SECTIONKINDS[self.TOC[i]['kind']]
			if previousdepth != currentdepth:
				if currentdepth == SECTIONKINDS['part']:	# Don't reset chap nums after new part
					for j in range(currentdepth + 2, len(index)): index[j] = 0
				else:
					for j in range(currentdepth + 1, len(index)): index[j] = 0
			if self.TOC[i]['kind'][-1] == '*' or self.TOC[i]['kind'] == 'paragraph' or self.TOC[i]['kind'] == 'subparagraph':
				self.TOC[i]['number'] = ''
			else:
				index[currentdepth] += 1
				if self.TOC[i]['kind'] == 'part':
					self.TOC[i]['number'] = ' ' + unicode(index[currentdepth])
				else:
					numberstring = ''
					for depth in range(3, currentdepth + 1):
						if numberstring == '': numberstring = unicode(index[depth])
						else: numberstring += '.' + unicode(index[depth])
					while numberstring.startswith('0.'): numberstring = numberstring[2:]
					self.TOC[i]['number'] = ' ' + numberstring
		self.find_section_line_numbers()

	def find_section_line_numbers(self):
		position = self.begin_document_position
		for headingnumber in range(len(self.TOC)):
			if self.TOC[headingnumber]['kind'] == 'title':
				foundposition = self.document.find('\\title')
			else: foundposition = self.document.find('\\' + self.TOC[headingnumber]['kind'], position)
			if foundposition == -1:
				print 'ERROR! Not finding all the headings in the document!'
				return
			foundposition = self.document.find(self.TOC[headingnumber]['title'], foundposition)
			if foundposition == -1:
				print 'ERROR! Not finding all the heading titles in the document!'
				return
			self.TOC[headingnumber]['position'] = position = foundposition

	def cites_to_treelist(self):
		self.citations = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		founditems = findall('\\\\[cC]ite(\\[.*?\\])?{(.*?)}', self.document[self.begin_document_position:])
		position = self.begin_document_position
		for item in founditems:
			pagerange, citation = item
			foundposition = self.document.find(citation, position)
			if foundposition == -1:
				print 'ERROR! Not finding all citations in the document!'
				return
			self.citations.append(dict(text = citation, position = foundposition, pagerange = pagerange[1:-1]))
			position = foundposition
		if self.sorted_status.get():
			self.citations = sorted(self.citations, key = lambda k: k['text'].lower())
		for i in range(len(self.citations)):
			self.treelist.insert('', 'end', unicode(i), text = self.citations[i]['text'], open = True)

	def crossrefs_to_treelist(self):
		self.labels_and_refs = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		tempCrossRefs = []
		foundlabels = findall('\\\\label{(.*?)}', self.document[self.begin_document_position:])
		foundrefs = findall('(\\\\\\w{0,5}ref){(.*?)}', self.document[self.begin_document_position:])
		refs_no_label = []
		position = self.begin_document_position
		for ref, label in foundrefs:
			if label not in foundlabels and label not in refs_no_label and ref != '\\xref':
				foundlabels.insert(0, label)
				refs_no_label.append(label)
		for label in foundlabels:
			labelposition = self.document.find('\\label{' + label + '}') + 7
			if labelposition == 6 and label not in refs_no_label:
				print 'ERROR! Not finding all labels in the document!'
				return
			reflist = []
			foundrefs = findall('\\\\\\w{0,5}ref{' + label + '}', self.document[self.begin_document_position:])
			position = self.begin_document_position
			for ref in foundrefs:
				refposition = self.document.find(ref, position)
				refposition = self.document.find(label, refposition)
				if refposition == -1:
					print 'ERROR! Not finding all references in the document!'
					return
				reflist.append(refposition)
				position = refposition
			tempCrossRefs.append(dict(label = label, position = labelposition, refs = reflist, nolabel = label in refs_no_label))
		if self.sorted_status.get():
			tempCrossRefs = sorted(tempCrossRefs, key = lambda k: k['label'].lower())
		treenum = 0
		for index in range(len(tempCrossRefs)):
			if tempCrossRefs[index]['nolabel']:
				self.treelist.insert('', 'end', unicode(treenum), text = tempCrossRefs[index]['label'], open = True, tags = 'greyed_out')
				self.labels_and_refs.append(-1)
			else:
				self.treelist.insert('', 'end', unicode(treenum), text = tempCrossRefs[index]['label'], open = True)
				self.labels_and_refs.append(tempCrossRefs[index]['position'])
			parent = unicode(treenum)
			treenum += 1
			for j in tempCrossRefs[index]['refs']:
				if tempCrossRefs[index]['nolabel']:
					self.treelist.insert(parent, 'end', unicode(treenum), text = 'Ref: ' + tempCrossRefs[index]['label'], tags = 'empty')
				else:
					self.treelist.insert(parent, 'end', unicode(treenum), text = 'Ref: ' + tempCrossRefs[index]['label'])
				self.labels_and_refs.append(j)
				treenum += 1
		if self.sorted_status.get(): self.sort_ref_treelist()

	def sort_ref_treelist(self):
		labellist = ['app', 'cha', 'eq', 'fig', 'itm', 'lst', 'par', 'sec', 'sub', 'tab']
		labelorder = ['Parts', 'Chapters', 'Sections', 'Subsections', 'Appendices', 'Figures', 'Tables', 'Equations', 'Items', 'Listings']
		labelname = ['Appendices', 'Chapters', 'Equations', 'Figures', 'Items', 'Listings', 'Parts', 'Sections', 'Subsections', 'Tables']
		for item in range(len(labelorder)):
			self.treelist.insert('', item, labelorder[item], text = labelorder[item], open = True, tags = 'greyed_out')
		counter = 0
		for item in self.treelist.get_children():
			prefix = self.treelist.item(item)['text'].split(':')[0]
			while prefix > labellist[counter]:
				if counter < len(labellist) - 1: counter += 1
				else: break
			if prefix == labellist[counter]:
				self.treelist.move(item, labelname[counter], 'end')
		for item in labelname:
			if len(self.treelist.get_children(item)) == 0: self.treelist.delete(item)

	def footnotes_to_treelist(self):
		self.footnotes = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		footnotenumber = 0
		listnumber = 0
		position = self.begin_document_position
		while True:
			foundposition = self.document.find('\\footnote{', position) + 10
			if foundposition == 9: break
			footnotetext = get_brace_text(self.document[foundposition - 1:])
			position = foundposition + len(footnotetext)
			footnotenumber += 1
			if footnotenumber > 1:
				footnotenumber = check_footnote_reset(self.document[self.footnotes[-1]:position], footnotenumber)
			self.treelist.insert('', 'end', unicode(listnumber), text = unicode(footnotenumber) + '. ' + footnotetext)
			self.footnotes.append(foundposition)
			listnumber += 1

	def index_to_treelist(self):
		self.indices = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		position = self.begin_document_position
		while True:
			foundposition = self.document.find('\\index{', position) + 7
			if foundposition == 6: break
			indextext = get_brace_text(self.document[foundposition - 1:])
			self.indices.append(dict(text = indextext, position = foundposition))
			position = foundposition
		if self.sorted_status.get():
			self.indices = sorted(self.indices, key = lambda k: k['text'].lower())
		for i in range(len(self.indices)):
			self.treelist.insert('', 'end', unicode(i), text = self.indices[i]['text'])

	def todos_to_treelist(self):
		self.todos = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		todonumber = 0
		founditems = findall('(\\\\[mp]?todo|\\\\xref)({.*?})({.*?})?', self.document[self.begin_document_position:])
		position = self.begin_document_position
		for item in founditems:
			todonumber += 1
			type, first, second = item
			if second == '':
				foundposition = self.document.find(first, position)
			else:
				foundposition = self.document.find(second, position)
			if foundposition == -1:
				print 'ERROR! Not finding all todos in the document!'
				return
			foundtext = get_brace_text(self.document[foundposition:])
			if type == '\\xref': foundtext = 'Fix cross ref. ' + foundtext
			self.treelist.insert('', 'end', unicode(todonumber - 1), text = unicode(todonumber) + '. ' + foundtext)
			self.todos.append(foundposition + 1)
			position = foundposition + 1

	def figures_to_treelist(self):
		self.figures = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		figurenumber = 0
		position = self.begin_document_position
		while True:
			foundposition = self.document.find('\\begin{figure}', position)
			if foundposition == -1: break
			endfoundposition = self.document.find('\\end{figure}', foundposition)
			captionposition = self.document.find('\\caption', foundposition) + 8
			captionposition = self.document.find('{', captionposition)
			if captionposition == 7 or captionposition > endfoundposition:
				captiontext = ''
				captionposition = endfoundposition
			else: captiontext = get_brace_text(self.document[captionposition:])
			position = endfoundposition
			self.treelist.insert('', 'end', unicode(figurenumber), text = 'Figure ' + unicode(figurenumber + 1) + '. ' + captiontext)
			self.figures.append(captionposition + 1)
			figurenumber += 1

	def tables_to_treelist(self):
		self.tables = []
		x = self.treelist.get_children()
		for item in x: self.treelist.delete(item)
		tablenumber = 0
		position = self.begin_document_position
		while True:
			foundposition = self.document.find('\\begin{table}', position)
			if foundposition == -1: break
			endfoundposition = self.document.find('\\end{table}', foundposition)
			captionposition = self.document.find('\\caption', foundposition) + 8
			captionposition = self.document.find('{', captionposition)
			if captionposition == 7 or captionposition > endfoundposition:
				captiontext = ''
				captionposition = endfoundposition
			else: captiontext = get_brace_text(self.document[captionposition:])
			position = endfoundposition
			self.treelist.insert('', 'end', unicode(tablenumber), text = 'Table ' + unicode(tablenumber + 1) + '. ' + captiontext)
			self.tables.append(captionposition + 1)
			tablenumber += 1

	def item_selected(self, activate):
		'''
			When item in the self.treelist is selected, find the item number in the
			relevant list and run AppleScript to jump to that line in TeXShop.
		'''
		option = COMBOBOXENTRIES.index(self.combobox.get())
		itemname = self.treelist.focus()
		if not itemname.isdigit():
			self.treelist.bell()
			return
		item = int(itemname)
		if item >= 0:
			if option == 0:
				startposition = self.TOC[item]['position']
				selectionlength = len(self.TOC[item]['title'])
			elif option == 1:
				startposition = self.footnotes[item]
				selectionlength = len(self.treelist.item(itemname)['text']) - (self.treelist.item(itemname)['text'].find('.') + 2)
			elif option == 2:
				startposition = self.citations[item]['position']
				selectionlength = len(self.citations[item]['text'])
			elif option == 3:
				startposition = self.labels_and_refs[item]
				if startposition == -1:
					self.treelist.bell()
					return
				selectionlength = len(self.treelist.item(itemname)['text'])
				if self.treelist.item(itemname)['text'].startswith('Ref: '):
					selectionlength -= 5
			elif option == 4:
				startposition = self.todos[item]
				selectionlength = len(self.treelist.item(itemname)['text']) - (self.treelist.item(itemname)['text'].find('.') + 2)
				if self.treelist.item(itemname)['text'].find('. Fix cross ref.') > -1:
					startposition -= 6
					selectionlength -= 8
			elif option == 5:
				startposition = self.figures[item]
				selectionlength = len(self.treelist.item(itemname)['text']) - (self.treelist.item(itemname)['text'].find('.') + 2)
			elif option == 6:
				startposition = self.indices[item]['position']
				selectionlength = len(self.treelist.item(itemname)['text'])
			elif option == 7:
				startposition = self.tables[item]
				selectionlength = len(self.treelist.item(itemname)['text']) - (self.treelist.item(itemname)['text'].find('.') + 2)
			else:
				print 'ERROR! List selection out of range.'
				return
		else: return
		line = findline(self.document, startposition)
		cmd = """osascript <<EOT
tell application "TeXShop"
	open \"""" + self.filename.replace('/', ':')[1:] + """\"
	front document goto line """ + unicode(line) + """
	set offset of selection of front document to """ + unicode(startposition) + """
	set length of selection of front document to """ + unicode(selectionlength)
		if activate == True: cmd+= "\n   activate"
		cmd += "\nend tell\nEOT"
		system(cmd)

	def item_select_and_go(self, *args):
		'''
			This happens when user hits <Command-Return>. Passing True to item_selected
			inserts a command in the resulting AppleScript to bring TeXShop forward.
		'''
		self.item_selected(True)

	def sorted_pushed(self):
		self.populate_treelist()

	def refresh_pushed(self):
		self.refresh()

	def combobox_select(self, event):
		try:
			key = int(event.char)
			self.combobox.current(key - 1)
		except ValueError: pass
		self.populate_treelist()
		try:
			self.treelist.selection_set(0)
			self.get_last_tree_selected()
		except TclError: pass

	def get_last_tree_selected(self):
		self.last_branch_selected = self.treelist.selection()
		if len(self.last_branch_selected) > 0: self.last_branch_selected = self.last_branch_selected[0]
		else: self.last_branch_selected = ''

	def sorted_select(self, *args):
		if 'disabled' in self.sort_button.state():
			self.sort_button.bell()
		else:
			self.sort_button.invoke()

	def search_entered(self, *args):
		searchtext = self.search_field_text.get()
		self.get_last_tree_selected()
		self.populate_treelist()
		children = self.treelist.get_children()
		for child in children:
			if not self.find_in_treelist(child, searchtext):
				if child == self.last_branch_selected:
					self.last_branch_selected = self.find_surviving_parent(child)
				self.treelist.delete(child)
		self.treelist.selection_set(self.last_branch_selected)
		self.treelist.focus(self.last_branch_selected)

	def find_in_treelist(self, parent, searchtext):
		if searchtext.lower() in self.treelist.item(parent, 'text').lower():
			flag = True
			self.treelist.item(parent, tags = 'found')
		else:
			flag = False
			self.treelist.item(parent, tags = 'greyed_out')
		list = self.treelist.get_children(parent)
		if len(list) == 0: return flag
		for child in list:
			if self.find_in_treelist(child, searchtext):
				flag = True
			else:
				if child == self.last_branch_selected:
					self.last_branch_selected = self.find_surviving_parent(child)
				self.treelist.delete(child)
		return flag

	def find_surviving_parent(self, child):
		test = self.treelist.prev(child)
		if test != '': return test
		test = self.treelist.parent(child)
		if test != '': return test
		print 'Error selecting surviving sibling/parent'
		return ''

	def focus_search_box(self, *args):
		self.searchbox.focus_set()
		self.treelist.selection_set(self.last_branch_selected)
		self.treelist.focus(self.last_branch_selected)

	def graceful_close(self, *args):
		global WINDOWLIST
		save_window_geometry(self.window, self.filename)
		WINDOWLIST.remove(self)
		self.window.destroy()

def get_brace_text(text):
	'''
		Returns text in between curly braces starting at beginning of a string,
		but keeping all inner braces and text.
	'''
	text = text[text.find('{'):]
	if len(text) == 0:
		return 'ERROR: No braces found!'
	count = 0
	position = 0
	while True:
		a = text.find('{', position)
		b = text.find('}', position)
		if -1 < a < b:			# Next brace is '{'
			position = a + 1
			count += 1
		else:					# Next brace is '}' or not found
			if b == -1: return 'ERROR: No matching braces!'
			position = b + 1
			count -= 1
			if count == 0: return text[1:position - 1]

def findline(document, position):
	doclines = document.splitlines()
	count = 0
	for line in range(len(doclines)):
		count += len(doclines[line])
		if count > position: break
	return line

def check_footnote_reset(text, footnotenumber):
	if '\part' in text or '\chapter' in text: return 1
	return footnotenumber

def read_preferences():
	preferences = dict()
	try:
		file = open(PREFERENCES_FILE)
		preferences = load(file)
		file.close()
	except IOError: print 'I/O Error on reading preferences'
	return preferences

def write_preferences(preferences):
	try:
		file = open(PREFERENCES_FILE, 'wb')
		dump(preferences, file)
		file.close()
	except IOError: print 'I/O Error on writing preferences'

def save_window_geometry(window, filename):
	preferences = read_preferences()
	preferences[filename] = window.geometry()
	write_preferences(preferences)

def get_window_geometry_preferences(filename):
	preferences = read_preferences()
	try:
		return preferences[filename]
	except KeyError:
		return ''

def open_new_document(*args):
	filename = askopenfilename(filetypes = [('LaTeX files', '.tex')])
	if filename == '': return
	open_document(filename)

def open_document(filename):
	global WINDOWLIST
	for doc in WINDOWLIST:
		if filename == doc.filename:
			doc.window.grab_set()		# Bring window to top and take focus
			doc.window.grab_release()
			return
	new_document = DocumentStructure(ROOT, filename)
	WINDOWLIST.insert(0, new_document)

def open_TeXShop_document(*args):
	cmd =  "osascript -e 'tell application \"TeXShop\" \n   set newfile to path of front document\n   set newfile to quoted form of newfile\n   return newfile\nend tell'"
	(filename, tError) = Popen(cmd, shell = True, stdout = PIPE).communicate()
	filename = filename[1:-2]
	open_document(filename)

def graceful_quit(*args):
	preferences = read_preferences()
	for doc in WINDOWLIST:
		preferences[doc.filename] = doc.window.geometry()
	preferences['opendocs'] = [doc.filename for doc in WINDOWLIST]
	write_preferences(preferences)
	ROOT.destroy()

def open_last_documents(*args):
	preferences = read_preferences()
	try:
		for filename in preferences['opendocs']:
			open_document(filename)
	except KeyError: pass

def main():
	global ROOT
	ROOT = Tk()
	ROOT.wm_withdraw()
	ROOT.createcommand('exit', graceful_quit)

	open_last_documents()
	if WINDOWLIST == []: open_TeXShop_document()
	ROOT.mainloop()

if __name__ == '__main__': main()
