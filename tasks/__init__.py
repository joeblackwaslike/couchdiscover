import os
import glob

from invoke import Collection, task

from . import py, docker, test


collections = [py, docker, test]

ns = Collection()
for c in collections:
    ns.add_collection(c)

ns.configure(dict(
    project='couchdiscover',
    pwd=os.getcwd(),
    docker=dict(
        user=os.getenv('DOCKER_USER'),
        org=os.getenv('DOCKER_ORG', os.getenv('DOCKER_USER', 'joeblackwaslike')),
        tag='%s/%s:latest' % (
            os.getenv('DOCKER_ORG', os.getenv('DOCKER_USER', 'joeblackwaslike')),
            'couchdiscover'
        )
    )
))

@task
def templates(ctx):
    files = ' '.join(glob.iglob('templates/**.j2', recursive=True))
    ctx.run('tmpld --strict --data templates/vars.yaml {}'.format(files))

ns.add_task(templates)
