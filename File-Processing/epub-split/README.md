# EPUB File Splitter

Split a big `.epub` file into small ones so that Sony PRS-950 can read the files fast.

To split `fn.epub`, there must be a`fn.split` in the same directory of `fn.epub`, which contains the point where the file will be splitted. For example, the following file (`剑来.split`) specifies that new files will be starting from `Chapter0007.xhtml`, `Chapter0092.xhtml`, etc:

```
Chapter0007.xhtml
Chapter0092.xhtml
Chapter0187.xhtml
Chapter0249.xhtml
Chapter0307.xhtml
Chapter0372.xhtml
Chapter0469.xhtml
Chapter0530.xhtml
Chapter0587.xhtml
Chapter0702.xhtml
Chapter0765.xhtml
Chapter0853.xhtml
Chapter0977.xhtml
Chapter1058.xhtml
Chapter1240.xhtml
```

These splitting points come from table of content of the epub file, which can be viewed using `EpubSplit` plugin in `Calibre`. In Ubuntu, use the following command to install the latest `Calibre`:

```bash
sudo -v && wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin
```

- `split-epub.py`

  This script splits the epub according to the `.split` file.

- `950-split-epub.py`

  This script splits the epub according to the `.split` file. And further, it splits long chapters into small pieces so that PRS-950 can open the next chapter faster.
