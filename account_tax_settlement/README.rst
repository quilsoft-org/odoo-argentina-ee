.. |company| replace:: Q SOLUTIONS SA

.. |company_logo| image:: https://i.im.ge/2021/08/06/h7jo4.jpg
   :alt: Q SOLUTIONS SA
   :target: https://www.quilsoft.com

.. |icon| image:: https://i.im.ge/2021/08/06/h7xZW.jpg

.. image:: https://raster.shields.io/badge/license-AGPL--3-orange.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==============
Tax Settlement
==============

Módulo que implementa las siguientes funcionalidades:

* Nuevos campos en diarios genéricos para definir que son diarios de liquidación
* Crea nuevo menú para ver tablero de dichos diarios
* incorpora posibilidad de liquidar apuntes
* incorpora lógica genérica para generar archivos de liquidación (se requiere extender en módulos que terminen de implementarlo). Al principió los formateabamos con qweb pero vimos que quedan feos y, además, que no tiene tanto sentido ya que no es algo que sea necesario estar actualizando desde interfaz.


TODO migracion:
* tipo settlement a tipo general y setear impuesto
* Mas adelante podemos hacer que se liquide impuesto desde reportes con un botón como el de exportar (requiere un poco más de js y xml), ahora lo hacemos con una acción

Installation
============

To install this module, you need to:

#. Do this ...

Configuration
=============

To configure this module, you need to:

#. Go to ...

Usage
=====

To use this module, you need to:

Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://github.com/quilsoft-org/odoo-argentina-ee/wiki
