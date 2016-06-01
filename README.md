# Bombardier
Script for spamming requests to an URL in parallel

## Config
Bombardier supports providing it with a configuration file. Check out the example one to see how to build one. When adding blocks of text (`payload`, `headers` and `cookies` sections), REMEMBER to indent it.

`headers` and `cookies` need to be JSON-valid. `payload` doesn't.

You can provide it with a configuration file (`-c`/`--config` parameter) or directly with the URL to bombard (`-u`/`--url` parameter). In the latter case, GET requests will be performed.

If both `--config` and `--url` parameters are provided, `--config` takes precedence.

## Dependencies
Normal dependencies are listed in `requirements.txt`. Install them using `pip install -r requirements.txt`

If you also want nifty statistics (max, min, percentile, etc...) you also need `NumPy`: `pip install numpy`

As always, it's recommended to use virtualenvs.

## Usage
`bombardier.py --url $url-to-hit --threads $concurrent-threads --requests $requests-each-thread-will-launch`

or


`bombardier.py --config $config-file --threads $concurrent-threads --requests $requests-each-thread-will-launch`
