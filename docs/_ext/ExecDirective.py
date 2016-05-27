import sys
from os.path import basename

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from sphinx.util.compat import Directive
from sphinx.directives.code import CodeBlock
from docutils import nodes, statemachine
from sphinx.util.nodes import set_source_info

class ExecDirective(CodeBlock):
    """Execute the specified python code and insert the output into the document"""
    has_content = True
    required_arguments = 0

    def run(self):
        oldStdout, sys.stdout = sys.stdout, StringIO()

        tab_width = self.options.get('tab-width', self.state.document.settings.tab_width)
        source = self.state_machine.input_lines.source(self.lineno - self.state_machine.input_offset - 1)

        try:
            code = '\n'.join(self.content)
            exec(code)
            text = sys.stdout.getvalue()
        except Exception:
            return [nodes.error(None, nodes.paragraph(text = "Unable to execute python code at %s:%d:" % (basename(source), self.lineno)), nodes.paragraph(text = str(sys.exc_info()[1])))]
        finally:
            sys.stdout = oldStdout

        linespec = self.options.get('emphasize-lines')
        if linespec:
            try:
                nlines = len(self.content)
                hl_lines = [x+1 for x in parselinenos(linespec, nlines)]
            except ValueError as err:
                document = self.state.document
                return [document.reporter.warning(str(err), line=self.lineno)]
        else:
            hl_lines = None

        chevron_code = code.split('\n')
        chevron_code = [c for c in chevron_code if '#hide' not in c]
        chevron_code = '\n'.join([''.join(['>> ', line]) for line in chevron_code])

        if 'dedent' in self.options:
            lines = code.split('\n')
            lines = dedent_lines(lines, self.options['dedent'])
            code = '\n'.join([lines])

        lines = '\n'.join([chevron_code, text])

        literal = nodes.literal_block(lines, lines)
        # literal['language'] = 'python'
        literal['linenos'] = 'linenos' in self.options or \
                             'lineno-start' in self.options
        literal['classes'] += self.options.get('class', [])
        extra_args = literal['highlight_args'] = {}
        if hl_lines is not None:
            extra_args['hl_lines'] = hl_lines
        if 'lineno-start' in self.options:
            extra_args['linenostart'] = self.options['lineno-start']
        set_source_info(self, literal)

        caption = self.options.get('caption')
        if caption:
            self.options.setdefault('name', nodes.fully_normalize_name(caption))
            literal = container_wrapper(self, literal, caption)

        self.add_name(literal)

        return [literal]


def setup(app):
    app.add_directive('exec', ExecDirective)
