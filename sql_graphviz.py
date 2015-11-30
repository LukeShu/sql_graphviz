#!/usr/bin/env python2

import sys
from datetime import datetime
from pyparsing import \
    CharsNotIn, \
    Forward, \
    Literal, \
    OneOrMore, \
    Optional, \
    QuotedString, \
    Suppress, \
    Word, \
    ZeroOrMore, \
    alphanums, \
    alphas


def field_act(s, loc, tok):
    return ("<" + tok[0] + "> " + " ".join(tok)).replace("\"", "\\\"")


def field_list_act(s, loc, tok):
    return " | ".join(tok)


def create_table_act(s, loc, tok):
    return """
  "%(tableName)s" [
    label="<%(tableName)s> %(tableName)s | %(fields)s"
    shape="record" fillcolor="lightblue2" style="filled"
  ];""" % tok


def add_fkey_act(s, loc, tok):
    return """  "%(tableName)s":%(keyName)s -> "%(fkTable)s":%(fkCol)s""" % tok


def other_statement_act(s, loc, tok):
    return ""


def grammar():
    parenthesis = Forward()
    parenthesis <<= "(" + ZeroOrMore(CharsNotIn("()") | parenthesis) + ")"
    dontcare = Word(alphanums + "_\"'`:-") | parenthesis

    generic_word = Word(alphas + "`_") | QuotedString("\"")

    def_numeric_literal = generic_word
    def_name = generic_word
    def_type_name = OneOrMore(def_name) + Optional(Literal("(") + def_signed_number + ZeroOrMore(Suppress(",") + def_signed_number) + ")"
    def_foreign_table = generic_word
    def_table_name = generic_word
    def_schema_name = generic_word
    def_column_name = generic_word

    def_foreign_key_clause = Literal("REFERENCES") + def_foreign_table + \
                             Optional(Literal("(") + def_column_name + ZeroOrMore(Suppress(",") + def_column_name) + ")") + \
                             dontcare

    def_column_constraint = Optional(Literal("CONSTRAINT")+name()) + \
                            ( def_foreign_key_clause ) | dontcare)

    def_table_constraint = Optional(Literal("CONSTRAINT")+name()) + \
                           ( Literal("FOREIGN") + "KEY" + "(" def_column_name + ZeroOrMore(Suppress(",") + def_column_name ) + ")" + def_foreign_key_clause | dontcare )

    def_column_def = def_column_name + Optional(def_type_name) + def_column_constraint
    def_column_def.setParseAction(field_act)

    def_create_table_stmt = Literal("CREATE") + "TABLE" + \
                            Optional(def_schema_name + ".") + def_table_name + \
                            "(" def_column_def + ZeroOrMore(Suppress(",") + def_column_def) + ZeroOrMore(Suppress(",") + def_table_constraint) + ")"

    field_list_def = field_def + ZeroOrMore(Suppress(",") + field_def)
    field_list_def.setParseAction(field_list_act)

    create_table_def = Literal("CREATE") + "TABLE" + tablename_def.setResultsName("tableName") + "(" + field_list_def.setResultsName("fields") + ")" + ";"
    create_table_def.setParseAction(create_table_act)

    add_fkey_def = Literal("ALTER") + "TABLE" + "ONLY" + tablename_def.setResultsName("tableName") + "ADD" + "CONSTRAINT" + Word(alphanums + "_") + "FOREIGN" + "KEY" + "(" + Word(alphanums + "_").setResultsName("keyName") + ")" + "REFERENCES" + Word(alphanums + "_").setResultsName("fkTable") + "(" + Word(alphanums + "_").setResultsName("fkCol") + ")" + ";"
    add_fkey_def.setParseAction(add_fkey_act)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(other_statement_act)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(other_statement_act)

    return OneOrMore(comment_def | create_table_def | add_fkey_def | other_statement_def)


def graphviz(filename):
    print """/*"""
    print """/* Graphviz of '%s', created %s """ % (filename, datetime.now())
    print """ * Generated from https://github.com/rm-hull/sql_graphviz"""
    print """ */"""
    print """digraph g { graph [ rankdir = "LR" ]; """

    for i in grammar().parseFile(filename):
        if i != "":
            print i
    print "}"

if __name__ == '__main__':
    filename = sys.stdin if len(sys.argv) == 1 else sys.argv[1]
    graphviz(filename)
