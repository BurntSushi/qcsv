docs:
	scripts/generate-docs
	rsync -rh --inplace \
		doc/* \
		Geils:~/www/burntsushi.net/public_html/doc/qcsv/

pypi: docs
	sudo python2 setup.py register sdist bdist_wininst upload

pypi-meta:
	python2 setup.py register

pep8:
	pep8-python2 __init__.py

push:
	git push origin master
	git push github master

clean:
	sudo rm -rf build dist MANIFEST
