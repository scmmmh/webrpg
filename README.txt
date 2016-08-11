WebRPG README
=============

These instructions are for developers.

Setup virtual environment [once]
--------------------------------

- cd <directory containing this file>

- virtualenv --python=python3 .venv

Activate virtual environment
----------------------------

- source .venv/bin/activate

Setup development environment insive virtual environment [once]
---------------------------------------------------------------

- python setup.py develop

- WebRPG generate-config --filename development.ini

Create or upgrade database instance inside virtual environment
--------------------------------------------------------------

- WebRPG initialise-database development.ini

To automatically drop existing tables

- WebRPG initialise-database development.ini --drop-existing

Build GUI resources [once]
--------------------------

- cd src/gui
- npm install ember-cli bower
- npm install
- node_modules/.bin/bower install

Rebuild GUI resources [as necessary]
------------------------------------

- node_modules/.bin/ember build --output-path ../webrpg/gui/

Run this in the "src/gui" directory.

Activate service
----------------

- pserve development.ini --reload

Leave virtual environment
-------------------------

- deactivate
