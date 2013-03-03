import sublime
import sublime_plugin
import re

class GuessIndentationCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		#view.begin_edit()
		# patterns
		start_tag = '<\w+(?:\s+[^>\/]+)*\s*>'		# tag_start
		node_patterns = [start_tag, 
						start_tag[:-1]+'\/\s*>', 	# tag_empty
						'<\/\s?\w+\s?>', 			# tag_close
						'[^>\s][^<>]*[^<\s]']		# text_node
		patterns = '(?:{0})'.format('|'.join(node_patterns))
		indentors = re.compile('[ \t]*({0})'.format('|'.join(node_patterns[:1])))
		unindentors=re.compile('[ \t]*({0})'.format(node_patterns[2]))
		# process selected text
		for region in view.sel():
			# if selection contains text:
			if not region.empty():
				selection = view.substr(region)
				expanded = []
				# divide selected lines into XML elements, if it contains more than one
				for line in selection.split('\n'):
					elements = re.findall(patterns, line)
					if len(elements)>0:
						expanded += elements
					else:
						expanded.append(line)
				# indent output
				indent=0
				indented = []
				for line in expanded:
					match = unindentors.match(line)
					if match:
						indent = max(0, indent-1)
					# append line to output, unindented if closing tag
					indented.append('\t'*indent+line)
					if match:
						continue
					# test for possible indentation candidate
					# indentation applies to the NEXT line
					match = indentors.match(line)
					if match:
						indent+=1
				# replace selection with aligned output
				view.replace(edit, region, '\n'.join(indented))
