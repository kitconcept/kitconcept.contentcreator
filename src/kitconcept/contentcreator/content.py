# -*- coding: utf-8 -*-
from .interfaces import IHomepage
from plone.dexterity.content import Container
from zope.interface import implementer


@implementer(IHomepage)
class Homepage(Container):
  """Homepage content type"""
