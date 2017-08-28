from invoke import task


@task
def mkvenv(ctx, project=None):
    ctx.run(
        "mkvirtualenv -a $PWD -r requirements.txt %s" % (project or ctx.project))
    print('\nRemember to execute: workon %s' % (project or ctx.project))


@task
def develop(ctx):
    ctx.run("python3 setup.py develop")


@task
def build(ctx):
    ctx.run("python3 setup.py sdist bdist_wheel")


@task
def register(ctx):
    ctx.run("twine register dist/*.whl")


@task
def upload(ctx):
    ctx.run("twine upload dist/*")


@task
def clean(ctx):
    ctx.run("rm -rf build dist *.egg-info")


@task(build, register, upload, clean)
def publish(ctx):
    pass
