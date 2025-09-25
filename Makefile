
build:
	docker build -t ferranp/tinyerp .

run:
	docker run -d --publish-all=true --env-file=.env ferranp/tinyerp

runi:
	docker run -t -i --publish-all=true --env-file=.env ferranp/tinyerp

shell:
	docker run --rm -t -i ferranp/tinyerpnew /bin/bash
