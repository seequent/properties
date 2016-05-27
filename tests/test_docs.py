import subprocess
import unittest
import os

class Doc_Test(unittest.TestCase):

    @property
    def docs_dir(self):
        dirname, filename = os.path.split(os.path.abspath(__file__))
        return os.path.sep.join(dirname.split(os.path.sep)[:-1] + ['docs'])

    def setUp(self):
        self.build_dir = os.path.sep.join(self.docs_dir.split(os.path.sep) + ['_build'])
        if not os.path.isdir(self.build_dir):
            subprocess.call(["mkdir", "{0}".format(self.build_dir)])

        self.doctrees_dir = os.path.sep.join(self.build_dir.split(os.path.sep) + ['doctrees'])
        if not os.path.isdir(self.doctrees_dir):
            subprocess.call(["mkdir", "{0}".format(self.doctrees_dir)])

        self.html_dir = os.path.sep.join(self.build_dir.split(os.path.sep) + ['html'])
        if not os.path.isdir(self.html_dir):
            subprocess.call(["mkdir", "{0}".format(self.html_dir)])

    def test_html(self):
        # doctrees_path = os.path.sep.join(self.docs_dir.split(os.path.sep) + ['_build']+['doctrees'])
        # html_path = os.path.sep.join(self.docs_dir.split(os.path.sep) + ['_build']+['html'])

        check = subprocess.call(["sphinx-build", "-nW", "-b", "html", "-d",
            "%s"%(self.doctrees_dir) ,
            "%s"%(self.docs_dir),
            "%s"%(self.html_dir)])
        assert check == 0

    def test_linkcheck(self):
        # doctrees_path = os.path.sep.join(self.docs_dir.split(os.path.sep) + ['_build']+['doctrees'])
        # link_path = os.path.sep.join(self.docs_dir.split(os.path.sep) + ['_build'])

        check = subprocess.call(["sphinx-build", "-nW", "-b", "linkcheck", "-d",
            "%s"%(self.doctrees_dir),
            "%s"%(self.docs_dir),
            "%s"%(self.build_dir)])
        assert check == 0

if __name__ == '__main__':
    unittest.main()
