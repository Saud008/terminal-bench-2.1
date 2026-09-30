#include "hopcfg.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#define WHITESPACE " \t\r\n"
#define QUOTE "\""

/*
 * Return the next token of a configuration line and advance *s past it.
 * Tokens are separated by whitespace or by a single '='; a token may be
 * wrapped in double quotes.  Returns NULL on an unterminated quote.
 */
char *
strdelim(char **s)
{
	char *old;
	int wspace = 0;

	if (*s == NULL)
		return NULL;

	old = *s;
	*s = strpbrk(*s, WHITESPACE QUOTE "=");
	if (*s == NULL)
		return old;

	if (**s == '"') {
		memmove(*s, *s + 1, strlen(*s));
		if ((*s = strpbrk(*s, QUOTE)) == NULL)
			return NULL;
		**s = '\0';
		*s += strspn(*s + 1, WHITESPACE) + 1;
		return old;
	}

	if (**s == '=')
		wspace = 1;
	**s = '\0';

	*s += strspn(*s + 1, WHITESPACE) + 1;
	if (**s == '=' && !wspace)
		*s += strspn(*s + 1, WHITESPACE) + 1;

	return old;
}

/*
 * Split a string into arguments, honouring single and double quotes and
 * backslash escapes of quotes, backslashes and (outside quotes) spaces.
 * A '#' at the start of an argument ends the line when requested.
 */
int
argv_split(const char *s, int *argcp, char ***argvp, int terminate_on_comment)
{
	int argc = 0, quote, i, j;
	char *arg, **argv = xcalloc(1, sizeof(*argv));

	*argvp = NULL;
	*argcp = 0;

	for (i = 0; s[i] != '\0'; i++) {
		if (s[i] == ' ' || s[i] == '\t')
			continue;
		if (terminate_on_comment && s[i] == '#')
			break;
		quote = 0;

		argv = xreallocarray(argv, argc + 2, sizeof(*argv));
		arg = argv[argc++] = xcalloc(1, strlen(s + i) + 1);
		argv[argc] = NULL;

		for (j = 0; s[i] != '\0'; i++) {
			if (s[i] == '\\') {
				if (s[i + 1] == '\'' || s[i + 1] == '"' ||
				    s[i + 1] == '\\' ||
				    (quote == 0 && s[i + 1] == ' ')) {
					i++;
					arg[j++] = s[i];
				} else
					arg[j++] = s[i];
			} else if (quote == 0 && (s[i] == ' ' || s[i] == '\t'))
				break;
			else if (quote == 0 && (s[i] == '"' || s[i] == '\''))
				quote = s[i];
			else if (quote != 0 && s[i] == quote)
				quote = 0;
			else
				arg[j++] = s[i];
		}
		if (s[i] == '\0') {
			if (quote != 0) {
				argv_free(argv, argc);
				return -1;
			}
			break;
		}
	}
	*argcp = argc;
	*argvp = argv;
	return 0;
}

char *
argv_next(int *argcp, char ***argvp)
{
	char *ret = (*argvp)[0];

	if (*argcp > 0 && ret != NULL) {
		(*argcp)--;
		(*argvp)++;
	}
	return ret;
}

void
argv_consume(int *argcp)
{
	*argcp = 0;
}

void
argv_free(char **av, int ac)
{
	int i;

	if (av == NULL)
		return;
	for (i = 0; i < ac; i++)
		free(av[i]);
	free(av);
}

void
lowercase(char *s)
{
	for (; *s; s++)
		*s = tolower((unsigned char)*s);
}

/* Same trimming ssh applies to ProxyJump values. */
void
rtrim(char *s)
{
	size_t i;

	if ((i = strlen(s)) == 0)
		return;
	for (i--; i > 0; i--) {
		if (isspace((unsigned char)s[i]))
			s[i] = '\0';
	}
}
