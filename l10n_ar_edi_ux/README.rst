.. |company| replace:: QUILSOFT

.. |company_logo| image:: https://i.im.ge/2021/08/06/h7jo4.jpg
   :alt: QUILSOFT
   :target: https://www.quilsoft.com

.. |icon| image:: https://i.im.ge/2021/08/06/h7xZW.jpg

.. image:: https://raster.shields.io/badge/license-AGPL--3-orange.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================================
Argentinian Electronic Invoicing UX
===================================

* Disable l10n_ar_ux view that add Argentinian Localization accounting settings and use the one added by l10n_ar_edi
* Logic to connecto to AFIP Padron using connection approach in enterprise module l10n_ar_edi

About Padron:

#. If you want to disable Title Case for afip retrived data, you can change or create a paremeter "use_title_case_on_padron_afip" with value False (by default title case is used)
#. para actualizar tenemos básicamente dos opciones:

    * Desde un partner cualquiera, si el mismo tiene configurado CUIT, entonces puede hacer click en el botón "Actualizar desde AFIP"
    * Hacerlo masivamente desde ""

#. Si estas en un ambiente de testing pueden utilizar estos CUITs de prueba para el padrón 'ws_sr_padron_a5' https://gist.github.com/zaoral/245ea456c53aef5c8d2f12a099d30909

Installation
============

To install this module, you need to:

#. Nothing to do

Configuration
=============

To configure this module, you need to:

#. Nothing to do

Usage
=====

To use this module, you need to:

Credits
=======

Images
------

* |company|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by |company|.

To contribute to this module, please visit https://github.com/quilsoft-org/odoo-argentina-ee/wiki
