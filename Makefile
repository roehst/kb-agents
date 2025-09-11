build:
	docker build . -t kb-agents

run:
	docker run -it --rm -v ${PWD}:/app --env-file .env --name kb-agents kb-agents /bin/bash