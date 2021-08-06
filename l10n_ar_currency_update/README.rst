.. |company| replace:: Q SOLUTIONS SA

.. |company_logo| image:: https://i.im.ge/2021/08/06/h7jo4.jpg
   :alt: Q SOLUTIONS SA
   :target: https://www.quilsoft.com

.. |icon| image:: https://i.im.ge/2021/08/06/h7xZW.jpg

.. image:: https://raster.shields.io/badge/license-AGPL--3-orange.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

================================
Argentinian Currency Rate Update
================================

This will add AFIP Web Service as your currency provider (official argentinian provider).

By default the automatic rate updates are inactive, you can active them by company
by going to *Accounting / Configuration / Settings* menu and there found and set
the *Interval* and *Next Run* date in the *Automatic Currecy Rates* section
(dont forget to click Save button)

When actived the currency rates of your companies will be updated automatically.
We recommend to use daily interval since AFIP update the rates daily.

The scheduled action that will be run to update the currency rates will be run
after 21 hours (GMT-3), this is required since the rates are published by
AFIP after 9 pm.

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Already configured to update currency rates one per day, you can change
   this configurations going to General Settings / Invoicing / Automatic
   currency Rates section.

Usage
=====

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

This module is maintained by the |company|.

To contribute to this module, please visit https://github.com/quilsoft-org/odoo-argentina-ee/wiki
