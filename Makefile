
build:
	docker.io build -t ferranp/tinyerp .

run:
	docker.io run -d --publish-all=true --env-file=.env ferranp/tinyerp

runi:
	docker.io run -t -i --publish-all=true --env-file=.env ferranp/tinyerp

shell:
	docker.io run -t -i ferranp/tinyerp /bin/bash
