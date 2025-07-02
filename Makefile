
build:
	docker build -t ferranp/tinyerpnew .

run:
	docker run -d --publish-all=true --env-file=.env ferranp/tinyerpnew

runi:
	docker run -t -i --publish-all=true --env-file=.env ferranp/tinyerpnew

shell:
	docker run --rm -t -i ferranp/tinyerpnew /bin/bash
