# Lambda Layers

Any modules required for the lambda scripts needs to be brought in using layers.

```
pip install --target layers/payment_hook requests
pip freeze --path layers/payment_hook > layers/payment_hook/requirements.txt
```

For more details: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
