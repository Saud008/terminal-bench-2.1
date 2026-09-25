# Fixture catalog

| path | role |
|------|------|
| `/app/project/CMakeLists.txt` | root list file, subdirs, overlay include |
| `/app/project/third_party/widget/CMakeLists.txt` | libfoo + libbar FetchContent |
| `/app/project/third_party/widget/gadget/CMakeLists.txt` | nested subdir + libbaz |
| `/app/project/cmake/WidgetHelpers.cmake` | included from gadget via relative path |
| `/app/project/bad/malformed/CMakeLists.txt` | invalid syntax for strict-parse failure (protected) |
| `/app/vendor-cache/*.tar.gz` | offline dependency archives |
| `/app/project/overlays/pinned.cmake` | GIT_COMMIT pin fields for hash audit |
| `/app/install` | prebuilt install tree from image build |

See `/app/docs/fetchcontent-contract.md` for audit pipeline order and ephemeral audit requirements.
