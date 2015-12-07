GitNOC
======

![Cumulative Blame Stravalib](https://raw.githubusercontent.com/wdm0006/gitnoc/master/img/gitnoc.png)

A simple dashboard with Git statistics for teams and organizations. Currently experimental (read: slow and poorly featured).
The aim is to have a simple UI that can run on local host and visualize the interesting project-level analytics made possible
by git-pandas. 

To start with, I am just throwing everything that makes even a little sense in there.

Built with: flask, nvd3, git-pandas.

How to Install
==============

For the python component: set up a virtualenv then:

 1. pip install -r requirements.txt

For the web components:

 1. Install NPM (brew install node)
 2. npm install -g bower
 3. bower install
 