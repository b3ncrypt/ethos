```
        ______ _   _
       |  ____| | | |
       | |__  | |_| |__   ___  ___
       |  __| | __| '_ \ / _ \/ __|
       | |____| |_| | | | (_) \__ \
       |______|\__|_| |_|\___/|___/
     Ethos V1 - Illuminating the Ledger

                 /\
                /  \
               /    \
              |------|
               \    /
                \  /
                 \/
```

# Ethos V1 - Ethereum Forensic Tracing Tool

Ethos V1 is a command-line Ethereum blockchain forensics tool that
automatically traces and maps the flow of funds from a target wallet
address across multiple hops using a breadth-first search traversal.
It produces structured CSVs and a GEXF graph file for visualisation.

## Requirements

- Python 3.11 or higher
- An Etherscan API key (free plan is sufficient):
  - Register at: https://etherscan.io/register
  - Generate an API key at: https://etherscan.io/myapikey

## Installation

1. Clone or extract the project files to a local directory.

2. Install all required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Open `config.py` and replace the placeholder with your Etherscan API key:

   ```python
   ETHERSCAN_API_KEY = "YOUR_API_KEY_HERE"
   ```

## Usage

Run the tool from the command line:

```
python ethos.py -a <target_address> [options]
```

### Arguments

| Argument    | Flag | Required | Default | Description                                    |
|-------------|------|----------|---------|------------------------------------------------|
| `--address` | `-a` | Yes      | -       | Target Ethereum wallet address                 |
| `--hops`    | `-H` | No       | 3       | Maximum hop depth                              |
| `--limit`   | `-l` | No       | 20      | Max transactions retrieved from wallet address |

Show help:

```
python ethos.py --help
```

### Example

```
python ethos.py -a 0xTargetAddressHere -H 6 -l 7
```

## Output

All output files are saved to a `forensic_results/` folder, automatically
created on first run. Each file is prefixed with the first characters of
the target address and a timestamp to prevent overwriting previous results.

| File                  | Description                                    |
|-----------------------|------------------------------------------------|
| `[prefix]_nodes.csv`  | Registry of all unique addresses discovered    |
| `[prefix]_edges.csv`  | All transaction links mapped during the scan   |
| `[prefix]_graph.gexf` | Full directed graph for visualisation in Gephi |

### Visualising the graph with Gephi (recommended)

1. Download and install Gephi: https://gephi.org/
2. Open Gephi and select `File > Open`
3. Select the generated `.gexf` file
4. Run a layout algorithm to render the graph (optional)

## Notes

- Do not share or commit your `config.py` file with a real API key
- The tool is scoped exclusively to the Ethereum mainnet
- The free Etherscan API tier supports 5 calls per second. Ethos V1 is
  designed to remain compliant with this limit automatically
- Increasing hop depth or transaction limit will increase runtime

## Project report

A write-up of the tool's design, implementation, and a case-study run
is available in [`docs/Ethos_Scripting_Report.pdf`](docs/Ethos_Scripting_Report.pdf).
Produced for *CMP320: Advanced Ethical Hacking* at Abertay University.
