tag:
	sed -Ei '' 's/__version__ = "[0-9]*\.[0-9]*\.[0-9]*"/__version__ = "$(v)"/g' release.py
	git tag -a $(v) -m "$(m)"

tag_push:
	git push origin --tags
