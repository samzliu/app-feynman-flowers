#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import urllib2
import json
import re
import string
from optparse import OptionParser
import pbclient


def task_formatter(app_config, row, n_answers):
    """
    Format a task 

    :arg integer app_id: Application ID in PyBossa.
    :returns: PyBossa Task INFO object
    :rtype: dict
    """
    # Each row has the following format
    # row[0] = Filename,
    # row[1] = Molecule Label,
    # row[2] = Image width in nm,
    # row[3] = Image heigh in nm,
    # row[4] = Bounding Box X1,
    # row[5] = Bounding Box Y1,
    # row[6] = Bounding Box width,
    # row[7] = Bounding Box height,
    # row[8] = Bounding Box X2,
    # row[9] = Bounding Box Y2,

    # Data for the tasks
    #data_url = 'http://www.ucl.ac.uk/~ucanchi/PyBossa/Data/FePc_Cu001/'
    data_url = 'http://www.ucl.ac.uk/~ucanchi/PyBossa/Data/DyPc2_Cu/'
    width = row[6]
    height = row[7]
    info = dict(question=app_config['question'],
                n_answers=int(n_answers),
                url_photo=data_url + row[0],
                molecule_label=row[1],
                #img_width=row[2],
                #img_height=row[3],
                bbox=[dict(x=row[4],y=row[5],width=width,height=height),
                      dict(x=row[8],y=row[9],width=width,height=height),
                    ])
    return info

if __name__ == "__main__":
    # Arguments for the application
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    # URL where PyBossa listens
    parser.add_option("-s", "--server", dest="api_url",
                      help="PyBossa URL http://domain.com/", metavar="URL")
    # API-KEY
    parser.add_option("-k", "--api-key", dest="api_key",
                      help="PyBossa User API-KEY to interact with PyBossa",
                      metavar="API-KEY")
    # Create App
    parser.add_option("-c", "--create-app", action="store_true",
                      dest="create_app",
                      help="Create the application",
                      metavar="CREATE-APP")
    # Update template for tasks and long_description for app
    parser.add_option("-t", "--update-template", action="store_true",
                      dest="update_template",
                      help="Update Tasks template",
                      metavar="UPDATE-TEMPLATE"
                     )

    # Update tasks question
    parser.add_option("-q", "--update-tasks",
                      dest="update_tasks",
                      help="Update Tasks n_answers",
                      metavar="UPDATE-TASKS"
                     )

    parser.add_option("-x", "--extra-task", action="store_true",
                      dest="add_more_tasks",
                      help="Add more tasks",
                      metavar="ADD-MORE-TASKS"
                      )
    # Modify the number of TaskRuns per Task
    # (default 30)
    parser.add_option("-n", "--number-answers",
                      dest="n_answers",
                      help="Number of answers per task",
                      metavar="N-ANSWERS"
                     )

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    (options, args) = parser.parse_args()

    # Load app details
    try:
        app_json = open('app.json')
        app_config = json.load(app_json)
        app_json.close()
    except IOError as e:
        print "app.json is missing! Please create a new one"
        exit(0)

    if not options.api_url:
        options.api_url = 'http://localhost:5000/'
    pbclient.set('endpoint', options.api_url)

    if not options.api_key:
        parser.error("You must supply an API-KEY to create an \
                      applicationa and tasks in PyBossa")
    else:
        pbclient.set('api_key', options.api_key)

    if not options.n_answers:
        options.n_answers = 30

    if (options.verbose):
        print('Running against PyBosssa instance at: %s' % options.api_url)
        print('Using API-KEY: %s' % options.api_key)

    if options.create_app:
        pbclient.create_app(app_config['name'],
                app_config['short_name'],
                app_config['description'])
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        app.long_description = open('long_description.html').read()
        app.info['task_presenter'] = open('template.html').read()
        app.info['thumbnail'] = app_config['thumbnail']
        app.info['tutorial'] = open('tutorial.html').read()

        pbclient.update_app(app)
        # Open the CSV file with the tasks
        import csv 
        #with open('BoundingBoxData.csv', 'rb') as csvfile:
        with open('ImageData.csv', 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            # Each row has the following format
            # Filename,
            # Molecule Label,
            # Image width nm,
            # Image heigh nm,
            # Bounding Box X1,
            # Bounding Box Y1,
            # Bounding Box width,
            # Bounding Box height,
            # Bounding Box X2,
            # Bounding Box Y2,
            # The width and height is the same for the second box
            for row in csvreader:
                task_info = task_formatter(app_config, row, options.n_answers)
                pbclient.create_task(app.id, task_info)
    else:
        if options.add_more_tasks:
            for row in csvreader:
                task_info = task_formatter(app_config, row, options.n_answers)
                pbclient.create_task(app.id, task_info)

    if options.update_template:
        print "Updating app template"
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        app.long_description = open('long_description.html').read()
        app.info['task_presenter'] = open('template.html').read()
        app.info['tutorial'] = open('tutorial.html').read()
        pbclient.update_app(app)

    if options.update_tasks:
        print "Updating task n_answers"
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        n_tasks = 0
        offset = 0
        limit = 100
        tasks = pbclient.get_tasks(app.id,offset=offset,limit=limit)
        while tasks:
            for task in tasks:
                print "Updating task: %s" % task.id
                if ('n_answers' in task.info.keys()):
                    del(task.info['n_answers'])
                task.n_answers = int(options.update_tasks)
                pbclient.update_task(task)
                n_tasks += 1
            offset = (offset + limit)
            tasks = pbclient.get_tasks(app.id,offset=offset,limit=limit)
        print "%s Tasks have been updated!" % n_tasks


    if not options.create_app and not options.update_template\
            and not options.add_more_tasks and not options.update_tasks:
        parser.error("Please check --help or -h for the available options")
