from invoke import task


@task(default=True)
def test(ctx):
    ctx.run("tmpld test/*.j2")


@task
def clean(ctx):
    ctx.run("rm -rf test/*.{conf,txt}")
