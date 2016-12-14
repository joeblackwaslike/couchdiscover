.PHONY: docs

init:
	pip3 install -r requirements.txt

test-publish:
	python3 setup.py register -r pypitest
	python3 setup.py sdist upload -r pypitest
	rm -rf build dist couchdiscover.egg-info

publish:
	python3 setup.py register -r pypi
	python3 setup.py sdist upload -r pypi
	rm -fr build dist couchdiscover.egg-info
