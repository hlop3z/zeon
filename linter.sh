NAME=src/zeon/

uvx ssort $NAME && \
uvx isort $NAME && \
uvx black $NAME && \
uvx ruff format $NAME && \
uvx mypy $NAME && \
uvx ruff-check $NAME && \
uvx pylint $NAME 