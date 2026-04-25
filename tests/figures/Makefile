#!/usr/bin/make -f

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

SHELL := /bin/bash

top_srcdir := $(shell cd ../.. ; pwd)

all: \
  graphs.svg

%.svg: \
  %.dot
	dot -T svg -o _$@ $<
	mv _$@ $@

check: \
  all

clean:
	@rm -f \
	  *.dot \
	  _*

graphs.dot: \
  $(top_srcdir)/ontology/generated-ontology.ttl \
  $(top_srcdir)/shapes/generated-shapes.ttl \
  $(top_srcdir)/tests/exemplars.ttl \
  $(top_srcdir)/src/graphs_dot.py
	source $(top_srcdir)/venv/bin/activate \
	  && python3 $(top_srcdir)/src/graphs_dot.py \
	    $(top_srcdir)/ontology/generated-ontology.ttl \
	    $(top_srcdir)/shapes/generated-shapes.ttl \
	    $(top_srcdir)/tests/exemplars.ttl \
	    > _$@
	mv _$@ $@
