#include "widget.h"
#include "foo.h"
#include "bar.h"
#include "baz.h"

int widget_answer(void) {
  return foo_answer() + bar_answer() + baz_answer();
}
