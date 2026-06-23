#include "elo_parser.hpp"
#include <iostream>
#include <iomanip> 

int main() {
    EloParser ep;
    auto db = ep.parse();

    std::cout << "========================================\n";
    std::cout << "      ELO DATABASE VERIFICATION         \n";
    std::cout << "========================================\n";
    std::cout << std::left << std::setw(15) << "COUNTRY CODE" 
              << std::setw(20) << "TOTAL MATCHES" << "\n";
    std::cout << "----------------------------------------\n";

	int i = 1;
    int total_matches_all_countries = 0;
    for (const auto& [country_code, matches] : db) {
        std::cout << i << ". " << ep.translator[country_code] 
                  << " played: " << matches.size() << "\n";
        
        total_matches_all_countries += matches.size();
		++i;
    }

    std::cout << "========================================\n";
    std::cout << "Total distinct countries parsed: " << db.size() << "\n";
    std::cout << "Total match records stored: " << total_matches_all_countries << "\n";
    std::cout << "========================================\n";

    std::cout << "\n[!] ANOMALY WARNINGS (Countries with suspiciously low match counts):\n";
    for (const auto& [country_code, matches] : db) {
        if (matches.size() < 10) {
            std::cout << " - " << ep.translator[country_code] << " only has " << matches.size() << " matches.\n";

			std::cout << ep.translator[country_code] << " played against: " << std::endl;
			for (const auto &elo : db[country_code]) {
				std::cout << ep.translator[elo.opponent_code] << std::endl;
			}
        }
    }

    return 0;
}
