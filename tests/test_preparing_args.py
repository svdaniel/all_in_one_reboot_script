from reboot_script.prepare_arguments import preparing_args


def test_correcting_arguments_success():
    to_validate = "Toto!, by:   melo; vyjit."
    returned_value = preparing_args.correcting_arguments(to_validate)
    assert 'Toto!' and 'by' and 'melo' and 'vyjit.' in returned_value
