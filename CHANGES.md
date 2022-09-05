Changelog
=========

5.0.6 (unreleased)
------------------

- Change README, CHANGES, CONTRIBUTOR to markdown. @ericof

- Use plone/code-analysis-action@v1 for Code Analysis @ericof

- Directly change blocks and blocks_layout in the root for Plone6 and above @steffenri


5.0.5 (2022-07-28)
------------------

- `content_creator_from_folder` now accepts an optional list `types_order`
  to prefer loading particular content types earlier @davisagli

- Improved logging to include the content type. @davisagli

- Refactored to use `pathlib` internally. @davisagli

5.0.4 (2022-07-26)
------------------

- Add a feature for linking translations using `translations.csv` @davisagli

- Add the option to disable creating image scales immediately
  by setting the `CREATOR_SKIP_SCALES` environment variable. @davisagli

- If the `id` in JSON doesn't match the id from the filename,
  prefer the one in the JSON. @davisagli


5.0.3 (2022-06-23)
------------------

- Don't swallow ValueError while importing a content item. @davisagli


5.0.2 (2022-04-21)
------------------

- Fix language when the deserialization dict does not contain a `language` key.
  This was hidden by the general `reindexObject` that was removed previously. @sneridagh


5.0.1 (2022-04-20)
------------------

- Remove "always reindex" on finish object, since that was happening twice (on creation and on edit) @sneridagh

- Fix on edit content issue notify event (the content was not being reindexed on deserialization) @sneridagh


5.0.0 (2022-04-13)
------------------

- Include kitconcept.api as dependency @ericof

- Drop support for Python 3.7 @ericof

- Remove buildout @ericof

- Update Github Actions @ericof

4.0.0 (2022-01-21)
------------------

Breaking:

- Remove support for Archetypes and Python 2. @sneridagh

- Refactor the creator to break by default. Added a scapehatch to not to break and for
  open a debug session on fail via `CREATOR_DEBUG` and `CREATOR_CONTINUE_ON_ERROR`
  environment variables. @sneridagh

3.3.0 (2022-01-11)
------------------

FEATURE:

- Add ability to exclude files from the file list (content_creator_from_folder) @sneridagh

INTERNAL:

- Move to latest 5.2.6 build @sneridagh


3.2.0 (2021-12-03)
------------------

- Guess content id if missing, taking into account that the content might already be there. @sneridagh


3.1.0 (2021-12-03)
------------------

- Use an improved logging infrasttructure @sneridagh

3.0.2 (2021-11-28)
------------------

- Use debug log level when generating image scales @timo

- Make log messages more consistent @timo

- Do not use colors for info messages @timo


3.0.1 (2021-11-11)
------------------

- Add classifiers to setup.py for Python 3.8, 3.9 and maturity. @timo

- Set effective date if the content `review_state` is `published` @sneridagh

3.0.0 (2021-11-10)
------------------


- Explicitly include dependencies (supporting pip installations) @ericof

- Use plone/setup-plone@v1.0.0 in Github actions @ericof

- Require plone.restapi 7.5.0 or superior (volto-slate blocks: resolveuid for links, transformer support) @ericof


2.1.0 (2021-10-13)
------------------

- New `do_not_edit_if_modified_after` option. Allows to not edit if the given date is lesser than the object modification date. @sneridagh

2.0.0 (2021-07-09)
------------------

Breaking:

- Use Slate as default text block @sneridagh


1.2.1 (2021-07-09)
------------------

Bugfix:

- Add refresh of the created content for updating the serialized blocks with the
  resolveuid information @sneridagh

Internal:

- Remove some unused imports [timo]
- Add flake8 check on CI [timo]


1.2.0 (2021-04-08)
------------------

- Black list `images` foder inside the create content folders @sneridagh
- Improve error detection and report @sneridagh

1.1.0 (2021-01-26)
------------------

- Improve content language detection if the field is not present @sneridagh
- Fix and improve language inferring in the editing of an existing content @sneridagh

1.0.6 (2020-05-08)
------------------

- Publish package on pypi. @timo

- Added the from a folder content creation. @sneridagh


1.0.5 (2019-11-22)
------------------

- Improve error reporting in create_item_runner. @timo


1.0.4 (2019-11-21)
------------------

- Re-release. @timo


1.0.3 (2019-05-06)
------------------

- Re-release. @sneridagh


1.0.2 (2019-05-06)
------------------

- Nothing changed yet.


1.0.1 (unreleased)
------------------

- Port to Python 3. @sneridagh

- Documentation. @sneridagh


1.0.0 (2019-03-26)
------------------

- Initial release. @kitconcept
