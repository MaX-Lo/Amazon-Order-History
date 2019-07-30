"""
defines a CLI for the project
"""
# pylint: disable=W0107
from __future__ import annotations

import datetime
import logging
from cmd import Cmd
from termcolor import colored
from typing import Tuple, List, Dict, Any

from scraping import dash_app, utils
from scraping.CustomExceptions import LoginError, PasswordFileNotFound, OrdersNotFound
from scraping.Scraper import Scraper
from scraping.utils import OptionType, ArgumentType


class Cli(Cmd):
    """
    CLI interface for the scraping module
    """

    def __init__(self) -> None:
        super().__init__()

        logger = logging.getLogger(__name__)

        self.prompt: str = colored("Scraping >> ", 'cyan')
        self.SCRAPING_OPTIONS: List[Tuple[str, OptionType, ArgumentType]] = [
            ('email', OptionType.REQUIRED, ArgumentType.SINGLE_STRING),
            ('password', OptionType.OPTIONAL, ArgumentType.SINGLE_STRING),
            ('start', OptionType.OPTIONAL, ArgumentType.SINGLE_INT),
            ('end', OptionType.OPTIONAL, ArgumentType.SINGLE_INT),
            ('headless', OptionType.OPTIONAL, ArgumentType.FLAG),
            ('no-headless', OptionType.OPTIONAL, ArgumentType.FLAG)]

        self.cmdloop()

    def emptyline(self) -> bool:
        """
        defines what happens on empty line input. If not specified Superclass will rerun last command
        """
        return True

    def default(self, line: str) -> bool:
        """
        defines what happens if command not recognized
        :param line: the input line
        """
        print(f'{line} is not a valid option here. See help for more')
        return True

    def preloop(self) -> None:
        """
        Little Banner presented on CLI start :)
        """
        print('================================================')
        print(r'/ ___) / __)(  _ \ / _\ (  _ \(  )(  ( \ / __)')
        print(r'\___ \( (__  )   //    \ ) __/ )( /    /( (_ \\')
        print(r'(____/ \___)(__\_)\_/\_/(__)  (__)\_)__) \___/')
        print('================================================')

    def completedefault(self, *ignored: List[str]) -> List[str]:
        """
        auto completion default
        :param ignored: ignored params
        :return: List with possible suggestions
        """
        return list(map(lambda option: option[0], self.SCRAPING_OPTIONS))

    def do_scrape(self, line: str) -> None:
        """
        defines what happens on scrape command. In this case it tries to run the Scraper
        :param line: inputline
        """
        args_dict: Dict[str, Any] = self._get_args(line)
        if self._scrape_check_args(args_dict):
            print("Starting to scrape...\n")
            try:
                Scraper(email=args_dict['email'], password=args_dict['password'], headless=args_dict['headless'],
                        start=args_dict['start'], end=args_dict['end'], extensive=True)
            except LoginError:
                pass
            except PasswordFileNotFound:
                pass
            except AssertionError:
                pass

    def complete_scrape(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """
        for auto completion inside the scrape command
        :param text: the word to complete (or better the beginning of the word obviously)
        :param line: the whole input line
        :param begidx: the start of the word on line
        :param endidx: end of the word on line
        :return: List with possible suggestions
        """
        return list(map(lambda option: f'{"-" if line[begidx - 1] != "-" else ""}'
                                       f'{"-" if line[begidx - 2] != "-" else ""}'
                                       f'{option[0]} ',
                        filter(lambda option: option[0].startswith(text.lower()) and f'--{option[0]}' not in line,
                               self.SCRAPING_OPTIONS)))

    def help_scrape(self) -> None:
        """
        defines the help documentation for the scrape command
        """
        print(f'Scrapes your amazon orders.\n'
              f'Available options:')
        for option in self.SCRAPING_OPTIONS:
            print(f'\t--{option[0]}:\t\t{"required" if option[1] == OptionType.REQUIRED else "optional"}')

        print(f'\nThe --password flag is only optional if there is a pw.txt in the project root folder')

    def do_dash(self, line: str) -> None:
        """
        executes the dash command
        :param line: command input line
        """
        args_dict: Dict[str, Any] = self._get_args(line)
        if self._are_all_rec_args_accepted(received_args=args_dict, accepted_args=[]) \
                and self._check_args_value_count(received_args=args_dict, accepted_args=[]):
            try:
                dash_app.main()
            except OrdersNotFound:
                pass

    @staticmethod
    def help_dash() -> None:
        """
        defines the help documentation for the dash command
        """
        print("Evaluates the orders.json (which is created by scrape) and displays it in the browser")

    @staticmethod
    def do_exit(*_) -> bool:
        """
        exits the CLI on exit command
        :param _: is ignored
        :return: True
        """
        return True

    def _scrape_check_args(self, args: Dict[str, Any]) -> bool:
        """
        checks if scraping arguments are valid. Also sets the defaults if not specified
        :param args: recognized args
        :return: True if they are valid, False if not
        """
        is_valid = True
        if not self._are_all_req_args_given(self.SCRAPING_OPTIONS, args):
            is_valid = is_valid and False
        if not self._are_all_rec_args_accepted(self.SCRAPING_OPTIONS, args):
            is_valid = is_valid and False
        if not self._check_args_value_count(self.SCRAPING_OPTIONS, args):
            is_valid = is_valid and False

        if 'email' in args.keys():
            email: str = args['email']
            if '@' not in email or '.' not in email:
                print(f'Email is not in valid format: {email}')
                is_valid = is_valid and False

        if 'headless' in args.keys() and 'no-headless' in args.keys():
            is_valid = is_valid and False

        args['end'] = args['end'] if 'end' in args.keys() else datetime.datetime.now().year
        args['start'] = args['start'] if 'start' in args.keys() else 2010
        args['password'] = args['password'] if 'password' in args.keys() else ""
        args['headless'] = True if 'headless' in args.keys() else False

        return is_valid

    @staticmethod
    def _arg_int_parsable(args: Dict[str, Any], arg_key: str) -> bool:
        """
        Checks if integer value is actual an integer. If so it parses it
        :param args: the dict of all received args
        :param arg_key: the arg_key of which value shall be parsed
        :return: If it was possible to parse the value
        """
        if arg_key in args.keys():
            try:
                args[arg_key] = int(args[arg_key])
            except ValueError:
                print(f'--{arg_key} value has to be integer, not {type(args[arg_key])}. | {args["start"]}')
                return False
        return True

    @staticmethod
    def _are_all_req_args_given(accepted_args: List[Tuple[str, OptionType, ArgumentType]],
                                received_args: Dict[str, Any]) -> bool:
        """
        check if all required args are in rec_args
        :param accepted_args: the args accepted
        :param received_args: the args the user inputs
        :return: True if all required aruments are in received_args
        """
        required_args: List[str] = list(
            map(lambda option: option[0], filter(lambda arg: arg[1] == OptionType.REQUIRED, accepted_args)))
        missing_req_args: List[str] = list(
            map(lambda arg: f'--{arg}', filter(lambda arg: arg not in received_args.keys(), required_args)))
        if missing_req_args:
            print(f'Required arguments not specified: {missing_req_args}')
            return False

        return True

    def _check_args_value_count(self, accepted_args: List[Tuple[str, OptionType, ArgumentType]],
                                received_args: Dict[str, str]) -> bool:
        """
        checks if the value count of each arg is valid. also checks if int values are actual integers and if so, parses them
        :param received_args: the args the user inputted
        :return: True if all args had the expected amounts of values and int are actual ints
        """
        args_value_count_valid: bool = True
        for acc_arg in accepted_args:
            if acc_arg[0] in received_args.keys():
                values: List[str] = list(filter(lambda arg_str: arg_str, received_args[acc_arg[0]].split(" ")))
                if acc_arg[2] == ArgumentType.FLAG and values:
                    print(
                        f'Flag parameter {acc_arg[0]} should not have a value{"s" if len(values) > 1 else ""}: {values}')
                    args_value_count_valid = args_value_count_valid and False
                elif (acc_arg[2] == ArgumentType.SINGLE_STRING or acc_arg[2] == ArgumentType.SINGLE_INT) and len(
                        values) != 1:
                    print(f'Excpected 1 parameter for {acc_arg[0]}, but: {values} were given.')
                    args_value_count_valid = args_value_count_valid and False
                elif acc_arg[2] == ArgumentType.SINGLE_INT and not self._arg_int_parsable(received_args, acc_arg[0]):
                    args_value_count_valid = args_value_count_valid and False
                elif (acc_arg[2] == ArgumentType.MULTI_STRING or acc_arg[2] == ArgumentType.MULTI_INT) and len(
                        values) <= 1:
                    print(
                        f'Excpected multiple parameter for {acc_arg[0]}, but only {len(values)} were given: {values}.')
                    args_value_count_valid = args_value_count_valid and False
                elif acc_arg[2] == ArgumentType.MULTI_INT:
                    for value in values:
                        if not utils.is_int_parsable(value):
                            args_value_count_valid = args_value_count_valid and False
                        else:
                            received_args[acc_arg[0]] = int(received_args[acc_arg[0]])

        return args_value_count_valid

    @staticmethod
    def _are_all_rec_args_accepted(accepted_args: List[Tuple[str, OptionType, ArgumentType]],
                                   received_args: Dict[str, Any]) -> bool:
        """
        checks if all inputted args are known
        :param accepted_args: the args accepted by the program
        :param received_args: the args inputted by the user
        :return: True if all inputted args are known
        """
        not_rec_args: List[str] = list(
            filter(lambda rec_arg: rec_arg not in map(lambda arg: arg[0], accepted_args), received_args.keys()))
        if not_rec_args:
            print(f'Unrecognized argument{"s" if len(not_rec_args) > 1 else ""}: {not_rec_args}')
            return False

        return True

    @staticmethod
    def _get_args(line: str) -> Dict[str, str]:
        """
        spilts the line in parameter and value strings
        :param line: cli input line
        :return: Dict with parameter as key and values as one string
        """
        line = f' {line}'
        args_dict: Dict[str, Any] = {}
        args = line.split(" --")[1:]

        for arg in args:
            arg_tuple = arg.split(" ")
            args_dict[arg_tuple[0]] = " ".join(arg_tuple[1:])

        return args_dict
