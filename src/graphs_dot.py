#!/usr/bin/env python3

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

"""
This script takes a graph file as input, and emits a Dot (Graphviz) file illustrating OWL ontologies' transitive import closure and noted import-incompatibilities; PROF Profile links (including profiling and conformance); and SHACL shapes graph links.

This script was originally drawn from CASE-Corpora's import_closure.py, from this state:
https://github.com/casework/CASE-Corpora/blob/94b53d60f87a897923dc6633f378af62ad5d21ad/src/import_closure.py
"""

__version__ = "0.2.0"

import argparse
import hashlib
import logging
import os
from functools import cached_property
from typing import Any, Sequence

import pydot
import rdflib
from pydot.classes import AttributeDict
from pydot.core import EdgeDefinition
from rdflib import DCTERMS, OWL, PROF, RDF, SH, URIRef

_logger = logging.getLogger(os.path.basename(__file__))

_PREFIXES_GRAPH = rdflib.Graph()
_PREFIXES_GRAPH.bind("dcterms", DCTERMS)
_PREFIXES_GRAPH.bind("owl", OWL)
_PREFIXES_GRAPH.bind("prof", PROF)
_PREFIXES_GRAPH.bind("rdf", RDF)
_PREFIXES_GRAPH.bind("sh", SH)


def gv_node_id_by_hashing(identifier: str) -> str:
    """
    This function returns a string safe to use as a Dot node identifier.  The main concern addressed is Dot syntax errors caused by use of colons in IRIs.  Adapted from case_prov.case_prov_dot.iri_to_gv_node_id.

    >>> x = rdflib.URIRef("urn:example:kb:x")
    >>> gv_node_id_by_hashing(x)
    '_b42f80365d50f29359b0a4d682366646248b4939a2b291e821a0f8bdaae4cd2a'
    """
    hasher = hashlib.sha256()
    hasher.update(str(identifier).encode())
    return "_" + hasher.hexdigest()


def safe_node_label(in_iri: URIRef) -> str:
    # Implement same quotation-forcing hack as in case_prov_dot.
    return "IRI - " + str(in_iri)


class ThingNode(pydot.Node):
    """
    A node following conventions of:
    https://www.w3.org/TR/2019/NOTE-dx-prof-20191218/#diagramconventions

    This top class "ThingNode" is so named to be as general as owl:Thing.
    """

    # ThingNode and TopEdge differ in how they provide a node (/edge)
    # label because of the (Python) subclass object-of-owl:versionIRI
    # not having a dedicated class IRI.
    class_label = "owl:Thing"

    def __init__(
        self,
        name: str = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("shape", "box")
        super().__init__(name, obj_dict, **attrs)


class OntologyNode(ThingNode):
    """
    A pydot Node specialization for illustrating owl:Ontology.
    """

    class_label = "owl:Ontology"


class OntologyVersionNode(ThingNode):
    """
    A pydot Node specialization for illustrating the object of an owl:versionIRI triple.
    """

    class_label = "owl:versionIRI object"

    def __init__(
        self,
        name: str = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("color", "#9B9B9B")
        super().__init__(name, obj_dict, **attrs)


class ProfileNode(ThingNode):
    """
    A pydot Node specialization for illustrating prof:Profile.
    """

    class_label = "prof:Profile"

    def __init__(
        self,
        name: str = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("fillcolor", "#9B9B9B")
        defaults_houser.setdefault("style", "filled")
        super().__init__(name, obj_dict, **attrs)


class StandardNode(ThingNode):
    """
    A pydot Node specialization for illustrating dcterms:Standard.
    """

    class_label = "dcterms:Standard"

    def __init__(
        self,
        name: str = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("shape", "note")
        super().__init__(name, obj_dict, **attrs)


class ShapesGraphNode(ThingNode):
    """
    A pydot Node specialization for illustrating a SHACL 1.2 ShapesGraph.
    """

    class_label = "sh:ShapesGraph (SHACL 1.2)"


class TopEdge(pydot.Edge):
    """
    A pydot Edge specialization aligned to some RDF property, stored as the class-variable cls.rdf_property.  This class serves as an inheritance root.
    """

    rdf_property = OWL.topObjectProperty

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("label", self.edge_label)
        super().__init__(src, dst, obj_dict, **attrs)

    @cached_property
    def edge_label(self) -> str:
        return _PREFIXES_GRAPH.namespace_manager.qname(self.rdf_property)


class ConformsToEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating dcterms:conformsTo.
    """

    rdf_property = DCTERMS.conformsTo

    pass


class BackwardCompatibleWithEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating owl:backwardCompatibleWith.
    """

    rdf_property = OWL.backwardCompatibleWith

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("color", "gray")
        defaults_houser.setdefault("style", "dashed")
        super().__init__(src, dst, obj_dict, **attrs)


class IncompatibleWithEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating owl:incompatibleWith.
    """

    rdf_property = OWL.incompatibleWith

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("color", "red")
        defaults_houser.setdefault("fontcolor", "red")
        defaults_houser.setdefault("style", "dashed")
        super().__init__(src, dst, obj_dict, **attrs)


class IsProfileOfEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating prof:isProfileOf.
    """

    rdf_property = PROF.isProfileOf

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("arrowhead", "vee")
        super().__init__(src, dst, obj_dict, **attrs)


class ImportsEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating owl:imports.
    """

    rdf_property = OWL.imports

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("arrowhead", "onormal")
        super().__init__(src, dst, obj_dict, **attrs)


class PriorVersionEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating owl:priorVersion.
    """

    rdf_property = OWL.priorVersion

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("color", "gray")
        defaults_houser.setdefault("style", "dashed")
        super().__init__(src, dst, obj_dict, **attrs)


class ShapesGraphEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating sh:shapesGraph.
    """

    rdf_property = SH.shapesGraph


class VersionIRIEdge(TopEdge):
    """
    A pydot Edge specialization for illustrating owl:versionIRI.
    """

    rdf_property = OWL.versionIRI

    def __init__(
        self,
        src: EdgeDefinition | Sequence[EdgeDefinition] = "",
        dst: EdgeDefinition = "",
        obj_dict: AttributeDict | None = None,
        **attrs: Any,
    ) -> None:
        defaults_houser = attrs if obj_dict is None else obj_dict
        defaults_houser.setdefault("color", "gray")
        super().__init__(src, dst, obj_dict, **attrs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("in_graph", nargs="+")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # rdflib graph, vs. pydot graph.
    rgraph = rdflib.Graph()
    pgraph = pydot.Graph()

    for in_graph in args.in_graph:
        _logger.debug("in_graph = %r.", in_graph)
        rgraph.parse(in_graph)

    ontology_reference: dict[URIRef, pydot.Node] = dict()

    edges: list[pydot.Edge] = []

    node_classes_for_legend: set[type[ThingNode]] = set()
    edge_classes_for_legend: set[type[TopEdge]] = set()

    # Find all ShapesGraph nodes.
    for triple in rgraph.triples((None, SH.shapesGraph, None)):
        assert isinstance(
            triple[2], URIRef
        ), "shapesGraph required (see SHACL-SHACL) to be identified by IRI."
        if triple[2] not in ontology_reference:
            ontology_reference[triple[2]] = ShapesGraphNode(
                gv_node_id_by_hashing(str(triple[2])), label=safe_node_label(triple[2])
            )
            node_classes_for_legend.add(ShapesGraphNode)

    # Find all ontology versionIRI-object nodes.
    for triple in rgraph.triples((None, OWL.versionIRI, None)):
        assert isinstance(triple[2], URIRef)
        ontology_reference[triple[2]] = OntologyVersionNode(
            gv_node_id_by_hashing(str(triple[2])), label=safe_node_label(triple[2])
        )
        node_classes_for_legend.add(OntologyVersionNode)

    for triple in rgraph.triples((None, RDF.type, PROF.Profile)):
        assert isinstance(triple[0], URIRef)
        ontology_reference[triple[0]] = ProfileNode(
            gv_node_id_by_hashing(str(triple[0])), label=safe_node_label(triple[0])
        )
        node_classes_for_legend.add(ProfileNode)

    # Illustrate all remaining nodes typed (potentially multiple-typed)
    # owl:Ontology with Ontology nodes.
    for triple in rgraph.triples((None, RDF.type, OWL.Ontology)):
        assert isinstance(triple[0], URIRef)
        ontology_reference[triple[0]] = OntologyNode(
            gv_node_id_by_hashing(str(triple[0])), label=safe_node_label(triple[0])
        )
        node_classes_for_legend.add(OntologyNode)

    for triple_pattern in [
        (None, DCTERMS.conformsTo, None),
        (None, OWL.backwardCompatibleWith, None),
        (None, OWL.imports, None),
        (None, OWL.incompatibleWith, None),
        (None, OWL.priorVersion, None),
        (None, OWL.versionIRI, None),
        (None, PROF.isProfileOf, None),
        (None, SH.shapesGraph, None),
    ]:
        edge_class = {
            DCTERMS.conformsTo: ConformsToEdge,
            OWL.backwardCompatibleWith: BackwardCompatibleWithEdge,
            OWL.imports: ImportsEdge,
            OWL.incompatibleWith: IncompatibleWithEdge,
            OWL.priorVersion: PriorVersionEdge,
            OWL.versionIRI: VersionIRIEdge,
            PROF.isProfileOf: IsProfileOfEdge,
            SH.shapesGraph: ShapesGraphEdge,
        }[triple_pattern[1]]
        for triple in rgraph.triples(triple_pattern):
            # OWL permits the ontology IRI to be a blank node.
            if not isinstance(triple[0], URIRef):
                continue
            assert isinstance(triple[2], URIRef), (
                "Object of a triple with predicate %s is not a URIRef.  This is assumed to be a data error.  Please do file a GitHub Issue if this is intended data behavior."
                % triple[1]
            )
            if triple[0] not in ontology_reference:
                ontology_reference[triple[0]] = OntologyNode(
                    gv_node_id_by_hashing(str(triple[0])),
                    label=safe_node_label(triple[0]),
                )
                node_classes_for_legend.add(OntologyNode)
            if triple[2] not in ontology_reference:
                ontology_reference[triple[2]] = OntologyNode(
                    gv_node_id_by_hashing(str(triple[2])),
                    label=safe_node_label(triple[2]),
                )
                node_classes_for_legend.add(OntologyNode)

            graph_edge = edge_class(
                ontology_reference[triple[0]],
                ontology_reference[triple[2]],
            )
            edges.append(graph_edge)
            edge_classes_for_legend.add(edge_class)

    legend_subgraph = pydot.Subgraph(
        "cluster_legend",
        label="Legend\nNote: edges in legend only show most general applicability.",
    )
    pgraph.add_subgraph(legend_subgraph)

    # Add used classes to legend.
    node_classes_used_for_edges_in_legend: set[type[ThingNode]] = set()
    for edge_class in sorted(edge_classes_for_legend, key=lambda x: x.rdf_property):
        legend_node_class_0, legend_node_class_1 = {
            ConformsToEdge: (ThingNode, StandardNode),
            BackwardCompatibleWithEdge: (OntologyNode, OntologyVersionNode),
            IncompatibleWithEdge: (OntologyNode, OntologyNode),
            IsProfileOfEdge: (ProfileNode, StandardNode),
            ImportsEdge: (OntologyNode, OntologyNode),
            PriorVersionEdge: (OntologyNode, OntologyVersionNode),
            ShapesGraphEdge: (OntologyNode, ShapesGraphNode),
            VersionIRIEdge: (OntologyNode, OntologyVersionNode),
        }[edge_class]

        legend_node_0 = legend_node_class_0(
            gv_node_id_by_hashing(
                str(edge_class.rdf_property) + "0" + legend_node_class_0.class_label
            ),
            label=legend_node_class_0.class_label,
        )
        legend_subgraph.add_node(legend_node_0)
        node_classes_used_for_edges_in_legend.add(legend_node_class_0)

        legend_node_1 = legend_node_class_1(
            gv_node_id_by_hashing(
                str(edge_class.rdf_property) + "1" + legend_node_class_1.class_label
            ),
            label=legend_node_class_1.class_label,
        )
        legend_subgraph.add_node(legend_node_1)
        node_classes_used_for_edges_in_legend.add(legend_node_class_1)

        legend_edge = edge_class(legend_node_0, legend_node_1)
        legend_subgraph.add_edge(legend_edge)

    for node_class in sorted(
        node_classes_for_legend - node_classes_used_for_edges_in_legend,
        key=lambda x: x.class_label,
    ):
        legend_node = node_class(
            gv_node_id_by_hashing(node_class.class_label), label=node_class.class_label
        )
        legend_subgraph.add_node(legend_node)

    for ontology_pnode in ontology_reference.values():
        pgraph.add_node(ontology_pnode)
    for edge in edges:
        pgraph.add_edge(edge)

    print(str(pgraph))


if __name__ == "__main__":
    main()
