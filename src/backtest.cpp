#include "elo_parser.hpp"

int main() {
	EloParser ep;
	ep.parse();
	ep.dump_data("../data/backtest/backtest.csv");

	return 0;
}

