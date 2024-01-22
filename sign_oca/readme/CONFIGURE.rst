There is a wizard (sign.oca.template.generate.multi) that can be used for any model needed, an example would be `maintenance_sign_oca`.

It would be necessary to set an action linked to the model with the code:

.. code-block:: xml

  model.action_sign_oca_template_generate_multi()

and code method:

.. code-block:: python

    def action_sign_oca_template_generate_multi(self):
      action = self.env.ref("sign_oca.sign_oca_template_generate_multi_act_window")
      result = action.read()[0]
      ctx = dict(self.env.context)
      ctx.update({"default_model": self._name})
      result["context"] = ctx
      return result

this would allow to create `sign.request` records for the selected records (in a tree view for example).
