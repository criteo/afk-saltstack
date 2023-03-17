# Developer guide

## PR vs feature requests

For a feature request, please create an issue before doing any PR.

The reason for this is simple: we are working very actively on the subject and you might work on an implementation already designed on our side.

## Requirements

**unit and functionals tests** are mandatory.

Please ensure you have run the following before pushing a commit:
  * `black` and `isort` (or `invoke reformat`)
  * `pylama` to run all linters

About the logic:
  * implementation must be done for all Network OS supported, with the same behaviour
  * the templates must be as simple as possible (max nested block: three levels)
  * the complexity should be in the state modules

## Coding style

Follow usual best practices:
  * document your code (inline and docstrings)
  * constant are in upper case
  * use comprehensible variable name
  * one function = one purpose
  * function name should define perfectly its purpose
