"""Hand-written case specs for gleaner's hidden tests. Expected output is recorded from git."""

BASE = "/tmp/gleaner-case"
HOME = BASE + "/user"
XDG = BASE + "/xdg"
DEFAULT_CONFIG = "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n"


def F(*paths):
    return {p: "x\n" for p in paths}


def case(name, files, checks, **kw):
    c = {"name": name, "files": files, "checks": checks}
    c.update(kw)
    return c


G = {}

G["file_encodings"] = [
    case("bom_and_crlf_root",
         {**F("a.log", "keep.log", "notes.txt", "build/out.bin", "src/build/x.c", "src/c.log", "src/main.c"),
          ".gitignore": "\ufeff*.log\r\n!keep.log\r\nbuild/\r\n"},
         ["a.log", "keep.log", "build", "build/out.bin", "src/c.log", "src/main.c", "notes.txt"]),
    case("crlf_in_subdir_last_line_unterminated",
         {**F("pkg/a.tmp", "pkg/b.o", "pkg/c.txt", "pkg/deep/d.tmp", "top.tmp", "pkg/cache/e"),
          "pkg/.gitignore": "# generated\r\n\r\n*.tmp\r\ncache/\r\n*.o\r"},
         ["pkg/a.tmp", "pkg/b.o", "pkg/deep/d.tmp", "pkg/cache", "pkg/cache/e", "top.tmp", "pkg/c.txt"]),
    case("bom_in_info_exclude_and_excludes_file",
         {**F("x.bak", "y.swp", "z.txt", "d/w.bak"), ".gitignore": "z.txt\n"},
         ["x.bak", "y.swp", "d/w.bak", "z.txt"],
         exclude="\ufeff*.bak\n",
         config=DEFAULT_CONFIG + "\texcludesFile = ~/global-ignore\n",
         home={"global-ignore": "\ufeff*.swp\r\n"}),
    case("crlf_negation_and_anchor",
         {**F("out/a.js", "out/keep/b.js", "lib/out/c.js", "readme.md", "docs/readme.md"),
          ".gitignore": "/out/*\r\n!/out/keep/\r\n/readme.md\r\n"},
         ["out/a.js", "out/keep", "out/keep/b.js", "lib/out/c.js", "readme.md", "docs/readme.md"]),
]

G["trailing_spaces"] = [
    case("spaces_tabs_and_escapes",
         {**F("trail", "trail ", "sp ", "sp", "tab", "two ", "two", "plain", "end"),
          ".gitignore": "trail   \nsp\\ \ntab\t\ntwo\\  \nend\\\n"},
         ["trail", "trail ", "sp ", "sp", "tab", "two ", "two", "end", "plain"]),
    case("escaped_space_in_directory_pattern",
         {**F("my dir /a", "my dir/b", "cache/c", "sub/cache/d", "logs /e", "logs/f"),
          ".gitignore": "cache/   \nlogs\\ /\nmy\\ dir\\ /\n"},
         ["my dir /a", "my dir/b", "cache/c", "sub/cache/d", "logs /e", "logs/f"]),
    case("tab_kept_in_subdir_file",
         {**F("w/k", "w/k2", "w/m", "k"),
          "w/.gitignore": "k\t\nk2 \t \nm \\\t\n"},
         ["w/k", "w/k2", "w/m", "k"]),
]

G["escaped_leading_characters"] = [
    case("literal_bang_and_hash",
         {**F("!important.txt", "important.txt", "#notes", "notes", "keep"),
          ".gitignore": "\\!important.txt\n\\#notes\n#keep\n"},
         ["!important.txt", "important.txt", "#notes", "notes", "keep"]),
    case("escaped_bang_after_glob",
         {**F("secret-a", "secret-keep", "!secret-keep", "other"),
          ".gitignore": "secret*\n\\!secret-keep\n"},
         ["secret-a", "secret-keep", "!secret-keep", "other"]),
    case("escaped_bang_in_subdir_and_real_negation",
         {**F("d/!x", "d/x", "d/y", "e/!x", "e/x"),
          "d/.gitignore": "*\n!.gitignore\n\\!x\n!x\n",
          "e/.gitignore": "\\!x\n"},
         ["d/!x", "d/x", "d/y", "d/.gitignore", "e/!x", "e/x"]),
]

G["directory_only_patterns"] = [
    case("trailing_slash_matches_at_any_depth",
         {**F("build/a", "src/build/b", "src/lib/build", "docs/logs/x", "logs", "tmp/y"),
          ".gitignore": "build/\nlogs/\n"},
         ["build", "build/a", "src/build", "src/build/b", "src/lib/build", "docs/logs", "docs/logs/x", "logs"]),
    case("dir_only_in_subdir_file",
         {**F("sub/a/tmp/z", "sub/tmp", "sub/b/tmp/q", "tmp/r", "other/tmp/s"),
          "sub/.gitignore": "tmp/\n"},
         ["sub/a/tmp", "sub/a/tmp/z", "sub/tmp", "sub/b/tmp", "tmp", "tmp/r", "other/tmp/s"]),
    case("negated_dir_only",
         {**F("out/a", "x/out/b", "y/cache/c", "y/cache2/d"),
          ".gitignore": "*/\n!x/\n!out/\n!y/\ncache/\n"},
         ["out", "out/a", "x", "x/out", "y", "y/cache", "y/cache2", "y/cache2/d"]),
]

G["anchoring"] = [
    case("middle_slash_anchors_to_file_directory",
         {**F("doc/frotz", "a/doc/frotz", "root-only", "x/root-only", "a/b.o", "doc/frotz.txt"),
          ".gitignore": "doc/frotz\n/root-only\n*.o\n"},
         ["doc/frotz", "a/doc/frotz", "root-only", "x/root-only", "a/b.o", "doc/frotz.txt"]),
    case("subdir_file_relative_paths",
         {**F("sub/gen/out.txt", "sub/x/gen/out.txt", "gen/out.txt", "sub/gen/other.txt"),
          "sub/.gitignore": "gen/out.txt\n"},
         ["sub/gen/out.txt", "sub/x/gen/out.txt", "gen/out.txt", "sub/gen/other.txt"]),
    case("leading_slash_in_subdir_file",
         {**F("pkg/top", "pkg/x/top", "top", "pkg/dist/a", "pkg/src/dist/b", "dist/c"),
          "pkg/.gitignore": "/top\n/dist/\n"},
         ["pkg/top", "pkg/x/top", "top", "pkg/dist", "pkg/dist/a", "pkg/src/dist/b", "dist/c"]),
    case("single_star_stays_in_one_component",
         {**F("a/b/c", "a/b/x/c", "z/a/b/c", "a/bb/c", "lib/v1/x.map", "src/lib/v1/y.map"),
          ".gitignore": "a/*/c\nlib/*/*.map\n"},
         ["a/b/c", "a/b/x/c", "z/a/b/c", "a/bb/c", "lib/v1/x.map", "src/lib/v1/y.map"]),
]

G["double_star"] = [
    case("star_star_inside_a_component",
         {**F("logs/2024/jan/raw", "logs/2024-old/x/raw", "logs/2024x/raw", "w/data/a1/b/c.csv", "w/data/a1/c.csv"),
          ".gitignore": "logs/202?**/raw\n",
          "w/.gitignore": "data/[a]**/*.csv\n"},
         ["logs/2024/jan/raw", "logs/2024-old/x/raw", "logs/2024x/raw", "w/data/a1/b/c.csv", "w/data/a1/c.csv"]),
    case("zero_or_more_directories",
         {**F("a/b", "a/x/b", "a/x/y/b", "a/xb", "b/a/b", "logs", "x/logs", "x/y/logs/z"),
          ".gitignore": "a/**/b\n**/logs\n"},
         ["a/b", "a/x/b", "a/x/y/b", "a/xb", "b/a/b", "logs", "x/logs", "x/y/logs", "x/y/logs/z"]),
    case("star_star_not_a_whole_component",
         {**F("foo/bar", "foo/x/bar", "fooz/bar", "a/bz/q", "bz/q", "a/b/z/q"),
          ".gitignore": "?oo**/bar\n**z/q\n"},
         ["foo/bar", "foo/x/bar", "fooz/bar", "a/bz/q", "bz/q", "a/b/z/q"]),
    case("trailing_and_triple_star",
         {**F("cache/a", "cache/d/e", "cache", "k/cache/f", "m/n/o/p", "m/p", "q/r/s"),
          ".gitignore": "/cache/**\nm/***/p\nq/**/\n"},
         ["cache/a", "cache/d", "cache/d/e", "k/cache/f", "m/n/o/p", "m/p", "q/r", "q/r/s"]),
]
# "cache" exists both as a directory (from cache/a) and would clash as a file; drop the file entry.
del G["double_star"][3]["files"]["cache"]

G["bracket_expressions"] = [
    case("caret_negation_and_leading_bracket",
         {**F("a.log", "b.log", "^.log", "x1", "]y", "zz", "cb", "ab", "]b"),
          ".gitignore": "[^a].log\n[]x]*\n[!]a]b\n"},
         ["a.log", "b.log", "^.log", "x1", "]y", "zz", "cb", "ab", "]b"]),
    case("posix_classes_and_ranges",
         {**F("1a", "a1", "Ax", "ax", "-", "b", "c", "v2.bin", "vx.bin"),
          ".gitignore": "[[:digit:]]*\n[[:upper:]]x\n[a-]\nv[^[:alpha:]].bin\n"},
         ["1a", "a1", "Ax", "ax", "-", "b", "v2.bin", "vx.bin"]),
    case("brackets_in_pathname_patterns",
         {**F("src/a1/x", "src/^1/x", "src/b1/x", "src/]/y", "src/a/y"),
          ".gitignore": "src/[^a]1/\nsrc/[]]/y\n"},
         ["src/a1/x", "src/^1/x", "src/b1", "src/b1/x", "src/]/y", "src/a/y"]),
]

G["reinclude_under_excluded_directory"] = [
    case("negation_cannot_rescue_file_in_excluded_dir",
         {**F("out/keep.txt", "out/x.o", "dist/keep.txt", "dist/y.o"),
          ".gitignore": "/out/\n!/out/keep.txt\n/dist/*\n!/dist/keep.txt\n"},
         ["out/keep.txt", "out/x.o", "dist/keep.txt", "dist/y.o", "out"]),
    case("basename_excluded_dir_with_negated_subdir",
         {**F("logs/important/a", "logs/b", "app/logs/important/c", "important/d"),
          ".gitignore": "logs\n!logs/important/\n!important/\n"},
         ["logs/important/a", "logs/important", "logs/b", "app/logs/important/c", "important/d"]),
    case("gitignore_inside_excluded_dir_is_not_read",
         {**F("vendor/lib/a.c", "vendor/lib/b.h", "vendor/c"),
          ".gitignore": "vendor/\n",
          "vendor/.gitignore": "!*\n",
          "vendor/lib/.gitignore": "!*.c\n"},
         ["vendor/lib/a.c", "vendor/lib/b.h", "vendor/c", "vendor/.gitignore"]),
]

G["per_directory_precedence"] = [
    case("deeper_negation_wins",
         {**F("sub/keep.tmp", "sub/x.tmp", "keep.tmp", "sub/deeper/keep.tmp"),
          ".gitignore": "*.tmp\n",
          "sub/.gitignore": "!keep.tmp\n"},
         ["sub/keep.tmp", "sub/x.tmp", "keep.tmp", "sub/deeper/keep.tmp"]),
    case("deeper_positive_beats_root_negation",
         {**F("important.log", "sub/important.log", "sub/other.log", "other.log"),
          ".gitignore": "*.log\n!important.log\n",
          "sub/.gitignore": "important.log\n"},
         ["important.log", "sub/important.log", "sub/other.log", "other.log"]),
    case("three_levels",
         {**F("a/b/c/f.gen", "a/b/f.gen", "a/f.gen", "f.gen", "a/b/c/g.gen"),
          ".gitignore": "!f.gen\n",
          "a/.gitignore": "*.gen\n",
          "a/b/c/.gitignore": "!f.gen\n"},
         ["a/b/c/f.gen", "a/b/f.gen", "a/f.gen", "f.gen", "a/b/c/g.gen"]),
]

G["tree_wide_sources"] = [
    case("info_exclude_beats_excludes_file",
         {**F("a.bak", "b.bak", "c.txt", "d.cache", "x.cache")},
         ["a.bak", "b.bak", "c.txt", "d.cache", "x.cache"],
         exclude="!a.bak\n*.cache\n",
         config=DEFAULT_CONFIG + "\texcludesFile = " + HOME + "/ignore-all\n",
         home={"ignore-all": "*.bak\n!x.cache\n"}),
    case("gitignore_beats_both",
         {**F("a.bak", "b.bak", "keep.cache", "z.cache"),
          ".gitignore": "!b.bak\n!keep.cache\n"},
         ["a.bak", "b.bak", "keep.cache", "z.cache"],
         exclude="*.cache\n",
         config=DEFAULT_CONFIG + "\texcludesFile = ~/.ignore\n",
         home={".ignore": "*.bak\n"}),
    case("relative_excludes_file",
         {**F("x.o", "y.o", "z.c"), ".gitignore": "!y.o\n", "tools/ignore": "*.o\n*.c\n"},
         ["x.o", "y.o", "z.c", "tools/ignore"],
         exclude="!x.o\n",
         config=DEFAULT_CONFIG + "\texcludesFile = tools/ignore\n"),
]

G["default_excludes_file"] = [
    case("xdg_config_home_wins",
         {**F("a.swp", "b.orig", "c.txt")},
         ["a.swp", "b.orig", "c.txt"],
         env={"XDG_CONFIG_HOME": XDG},
         xdg={"git/ignore": "*.swp\n"},
         home={".config/git/ignore": "*.orig\n"}),
    case("empty_xdg_falls_back_to_home",
         {**F("a.swp", "b.orig")},
         ["a.swp", "b.orig"],
         env={"XDG_CONFIG_HOME": ""},
         xdg={"git/ignore": "*.swp\n"},
         home={".config/git/ignore": "*.orig\n"}),
    case("xdg_without_ignore_file",
         {**F("a.swp", "b.orig")},
         ["a.swp", "b.orig"],
         env={"XDG_CONFIG_HOME": XDG},
         xdg={"git/config-only": "\n"},
         home={".config/git/ignore": "*.orig\n"}),
    case("configured_file_replaces_default",
         {**F("a.swp", "b.orig", "c.rej")},
         ["a.swp", "b.orig", "c.rej"],
         env={"XDG_CONFIG_HOME": XDG},
         config=DEFAULT_CONFIG + "\texcludesFile = ~/mine\n",
         xdg={"git/ignore": "*.swp\n"},
         home={".config/git/ignore": "*.orig\n", "mine": "*.rej\n"}),
]

G["config_spelling"] = [
    case("lowercase_key",
         {**F("a.log", "b.tmp")},
         ["a.log", "b.tmp"],
         config=DEFAULT_CONFIG + "\texcludesfile = ~/.gitignore_global\n",
         home={".gitignore_global": "*.log\n", ".config/git/ignore": "*.tmp\n"}),
    case("mixed_case_section_and_quoted_value",
         {**F("a.log", "b.tmp", "c.dat")},
         ["a.log", "b.tmp", "c.dat"],
         config=DEFAULT_CONFIG + "[Core]\n\tExcludesFile = \"~/ignore list\" ; user file\n",
         home={"ignore list": "*.dat\n", ".config/git/ignore": "*.tmp\n"}),
    case("last_assignment_wins",
         {**F("a.log", "b.tmp", "c.dat")},
         ["a.log", "b.tmp", "c.dat"],
         config=DEFAULT_CONFIG + "\texcludesFile = ~/first\n[user]\n\tname = x\n[core]\n\tEXCLUDESFILE = ~/second\n",
         home={"first": "*.log\n", "second": "*.dat\n"}),
]

G["list_order"] = [
    case("byte_order_of_whole_path",
         {**F("a-b", "a0", "a.b/c", "a b", "A", "a/b-c", "a/b/c", "a/b.d", "a+/x", "ab", "a!", "z.o"),
          ".gitignore": "*.o\n"},
         ["a/b", "a-b"]),
    case("order_across_nested_dirs",
         {**F("src/lib-x/a", "src/lib/b", "src/lib.rs", "src/lib/sub/c", "src/lib_y", "src-old/d", "src/e.tmp"),
          ".gitignore": "*.tmp\n"},
         ["src/e.tmp", "src/lib"]),
]

G["check_line_numbers"] = [
    case("comments_and_blank_lines_count",
         {**F("a.log", "b.tmp", "c.bak", "keep.log", "d/e.o"),
          ".gitignore": "# logs\n\n*.log\n\n# temp files\n*.tmp\n   \n!keep.log\n",
          "d/.gitignore": "\n\n# objects\n*.o\n"},
         ["a.log", "b.tmp", "c.bak", "keep.log", "d/e.o"],
         exclude="# git ls-files --others --exclude-from=.git/info/exclude\n# Lines that start with '#' are comments.\n*.bak\n"),
    case("line_numbers_in_excludes_file",
         {**F("x.swp", "y.orig")},
         ["x.swp", "y.orig"],
         config=DEFAULT_CONFIG + "\texcludesFile = ~/g\n",
         home={"g": "# editor\n\n\n*.swp\n# merge\n\n*.orig\n"}),
]
