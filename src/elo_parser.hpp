#include <execution>
#include <stdexcept>
#include <string>
#include <chrono>
#include <sstream>
#include <utility>
#include <vector>
#include <fstream>
#include <iostream>
#include <map>

/* THE PLAN 
 * 1. Seperate the timelines, the main timeline should 
 * contain EVERY single match and calculate variables from 
 * there. 
 * 2. The second timeline is the stat model timeline, no 
 * "Friendly" matches. */ 

struct Elo {
	int year, month, day;
	int elo, opp_elo;
	int days_passed; 
	int goals, conceded;
	bool home_advantage;

	bool friendly;
	std::string opponent_code;
	std::string team_us, team_opp; 
};

// string is the country code 
using db = std::map<std::string, std::vector<Elo>>;

class EloParser {
	private:
	db historical_elo_records;
	db model_elo_records;

	// translates country name to country code
	public:
	std::map<std::string, std::string> translator; 
	std::vector<std::string> world_cup_countries; 

	private:
	std::vector<std::string> get_all_countries() {
		std::ifstream countries_file("../data/backtest/all_countries_tsv");
		std::vector<std::string> all_countries;

		std::string country;
		while (countries_file >> country) {
			all_countries.push_back(country);
		}

		return all_countries;
	}

	public:
	void parse_codes() {
        std::ifstream countries_file("../data/en.teams.tsv");

        std::string line;
        while (std::getline(countries_file, line)) {
            std::stringstream ss(line);
            std::string code, name;

            if (std::getline(ss, code, '\t')) {
                std::getline(ss, name, '\t');
                translator[code] = name;
            }
        }	
	}

	public:
	void parse_world_cup_countries() {
		const std::string path = 
			"../data/backtest/normalized_countries";
		std::ifstream world_cup_countries_file(path);
		
		std::string line; 
		while (std::getline(world_cup_countries_file, line)) {
			world_cup_countries.push_back(line);
		}
	}

	private:
	void parse_country(const std::string &path, const std::string &country_name) {
		std::ifstream country_file(path);
		std::string line;

		while (std::getline(country_file, line)) {
			std::stringstream ss(line);
			std::string token;
			std::vector<std::string> cols;

			while (std::getline(ss, token, '\t')) {
				cols.push_back(token);
			}

			int year = std::stoi(cols.at(0));
			int month = std::stoi(cols.at(1));
			int day = std::stoi(cols.at(2));

			if (!((year == 2022 and month == 11 and day >= 20) or (year == 2022 and month == 12 and day <= 18))) {
				continue;
			}

			std::string us = cols.at(3);
			std::string enemy = cols.at(4);

			int us_goals = std::stoi(cols.at(5));
			int enemy_goals = std::stoi(cols.at(6));

			bool home_advantage; 
			if (!cols.at(8).empty()) {
				home_advantage = false;
			} else {
				home_advantage = true;
			}

			int us_elo = std::stoi(cols.at(10)) - std::stoi(cols.at(9));
			int enemy_elo = std::stoi(cols.at(11)) + std::stoi(cols.at(9));
			
			if (translator[us] != country_name) {
				std::swap(us, enemy);
				std::swap(us_goals, enemy_goals);
				std::swap(us_elo, enemy_elo);
				home_advantage = false;
			}

			Elo elo; 

			if (cols.at(7) == "F") {
				elo.friendly = true;
			} else {
				elo.friendly = false;
			}

			elo.elo = us_elo;
			elo.goals = us_goals;
			elo.opp_elo = enemy_elo;
			elo.year = year;
			elo.month = month;
			elo.day = day;
			elo.opponent_code = enemy;
			elo.home_advantage = home_advantage;
			historical_elo_records[us].push_back(elo);

			if ((us == "HR" && enemy == "MA") || (us == "MA" && enemy == "HR")) {
    std::cerr << "us=" << us << " enemy=" << enemy 
              << " us_goals=" << us_goals << " enemy_goals=" << enemy_goals
              << " elo=" << us_elo << " date=" << year << "-" << month << "-" << day 
              << std::endl;
}
		}
	}

	private:
	std::string delete_extension(const std::string &s) {
		std::string n_s = "";
		for (const auto &ch : s) {
			if (ch == '.') {
				break;
			} else if (ch == '_') {
				n_s += ' ';
				continue;
			}

			n_s += ch; 
		}

		return n_s;
	}
	
	private:
	void fill_model_db(const std::string &cc, const std::vector<Elo> &historical_data) {
		auto prev = historical_data.at(0);
		prev.days_passed = 10;

		if (!prev.friendly) {
			model_elo_records[cc].push_back(prev);
		}

		for (int i = 1; i < historical_data.size(); i++) {
			auto record = historical_data.at(i);
			auto date_post = (std::chrono::year(record.year)/
						      std::chrono::month(record.month)/
							  std::chrono::day(record.day));
			auto date_prev = (std::chrono::year(prev.year)/
					          std::chrono::month(prev.month)/
							  std::chrono::day(prev.day));
			auto datediff = static_cast<std::chrono::sys_days>(date_post) 
						  - static_cast<std::chrono::sys_days>(date_prev);

			record.days_passed = static_cast<unsigned>(datediff.count());

			// Capping at 10
			if (record.days_passed > 10) {
				record.days_passed = 10;
			}

			if (!record.friendly) {
				model_elo_records[cc].push_back(record);
			}

			prev = record;
		}
	}

	public:
	db parse() {
		parse_world_cup_countries();
		parse_codes(); // country code translation

		// These are only the initial parses - 1. from the plan
		const std::string path = "../data/backtest/";
		for (const auto &country : get_all_countries()) {
			std::string curr_path = path + country;
			parse_country(curr_path, delete_extension(country));
		}

		for (const auto &[cc, data_arr] : historical_elo_records) {
			fill_model_db(cc, data_arr);
		}

		return model_elo_records;
	}

	private:
	int get_opp_days_passed(const std::string &cc, const Elo &elo) {
		if (model_elo_records[elo.opponent_code].empty()) {
			return 10;
		}

		for (const auto &opp : model_elo_records[elo.opponent_code]) {
			if (opp.year == elo.year and opp.month == elo.month 
				and opp.day == elo.day and opp.opponent_code == cc) {
				return opp.days_passed;
			}
		}

		throw std::runtime_error("Opponent is found, yet no record of match.");
	}
	

	private:
	// ymd in chrono is cursed and I won't use it more than necessary
	struct Date {  
		int year, month, day; 
	};
	
	private:
	Date parse_date(const std::string &s_date) {
		Date date; 
		std::string curr = "";
			
		int i = 0;
		for (; s_date.at(i) != '-'; i++) {
			curr += s_date.at(i);	
		}

		++i;
		date.year = std::stoi(curr);
		curr = "";

		for (; s_date.at(i) != '-'; i++) {
			curr += s_date.at(i);
		}

		++i;
		date.month = std::stoi(curr);
		curr = "";

		for (; i < s_date.length(); i++) {
			curr += s_date.at(i);
		}

		date.day = std::stoi(curr);
		return date;
	}

	public:
	std::vector<Elo> parse_dixon_coles(const std::string &relative_path) {
		std::ifstream data(relative_path);
		std::string line;
		std::vector<Elo> parsed;

		while (std::getline(data, line)) {
			std::stringstream ss(line);
			std::string token;
			std::vector<std::string> cols;

			while (std::getline(ss, token, '\t')) {
				cols.push_back(token);
			}

			if (cols.at(5) == "Friendly") {
				continue; 
			}

			auto date = parse_date(cols.at(0));

			Elo elo_us, elo_opp;
			elo_us.goals = std::stoi(cols.at(3));
			elo_us.team_us = cols.at(1);
			elo_us.team_opp = cols.at(2);

			if (elo_us.team_us == cols.at(7)) {
				elo_us.home_advantage = true;
			} else {
				elo_us.home_advantage = false; 
			}

			elo_opp.goals = std::stoi(cols.at(4));
			elo_opp.team_us = cols.at(2);
			elo_opp.team_opp = cols.at(1);

			if (elo_opp.team_us == cols.at(7)) {
				elo_opp.home_advantage = true;
			} else {
				elo_opp.home_advantage = false; 
			}

			elo_us.year = date.year;
			elo_us.month = date.month;
			elo_us.day = date.day;

			elo_opp.year = date.year;
			elo_opp.month = date.month;
			elo_opp.day = date.day;
			
			parsed.push_back(elo_us);
			parsed.push_back(elo_opp);

			/*
			std::cout << "Elo_us:" << std::endl;
			std::cout << elo_us.goals << std::endl;
			std::cout << elo_us.team_us << std::endl;
			std::cout << elo_us.team_opp << std::endl;
			std::cout << elo_us.home_advantage << std::endl;

			std::cout << "Elo_opp:" << std::endl;
			std::cout << elo_opp.goals << std::endl;
			std::cout << elo_opp.team_us << std::endl;
			std::cout << elo_opp.team_opp << std::endl;
			std::cout << elo_opp.home_advantage << std::endl;
			*/
		}
		
		data.close();
		return parsed; 
	}

	public:
	void dump_data(const std::string &relative_path) {
		std::ofstream file(relative_path);

		for (const auto &[cc, elo_arr] : model_elo_records) {
			for (const auto &elo : elo_arr) {
				file << cc << ';'
					 << elo.opponent_code << ';'
					 << elo.goals << ';'
					 << elo.elo - elo.opp_elo << ';'
					 << elo.days_passed - get_opp_days_passed(cc, elo) << ';'
					 << elo.home_advantage << std::endl;
			}
		}

		file.close();
	}

	public:
	void dump_dixon_coles_data(const std::vector<Elo> &parsed, const std::string &relative_path) {
		std::ofstream file(relative_path); 

		for (const auto &elo : parsed) {
			file << elo.year		   <<  ';'
				 << elo.month		   <<  ';'
				 << elo.day			   <<  ';'
				 << elo.team_us		   <<  ';'
				 << elo.team_opp	   <<  ';'
				 << elo.goals		   <<  ';'
				 << elo.home_advantage << std::endl;
		}

		file.close();
	}
};

