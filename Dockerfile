# install pybicpl into an image with CIVET pre-installed,
# using conda to provide a recent-ish version of Python 3
# and cross-platform numpy.

FROM docker.io/fnndsc/civet:2.1.1 as base
FROM base as installer

RUN apt-get update && apt-get install -y curl

WORKDIR /tmp

ARG CONDA_VERSION=4.10.3
ARG PYTHON_VERSION=py39

RUN curl -so install-conda.sh \
    https://repo.anaconda.com/miniconda/Miniconda3-${PYTHON_VERSION}_${CONDA_VERSION}-$(uname -s)-$(uname -m).sh
RUN bash install-conda.sh -b -p /opt/conda

FROM base
COPY --from=installer /opt/conda /opt/conda
ENV PATH=/opt/conda/bin:$PATH

RUN conda config --prepend channels conda-forge
RUN conda install numpy=1.22.0

WORKDIR /usr/local/src/pybicpl
COPY . .
RUN pip install .
