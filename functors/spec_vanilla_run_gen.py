

def generate(benchmark, **kwargs):
    util = kwargs['util']

    ba = util.load_functor(['./examples', 'spec_arguments'])
    args = ba.benchmark_args[benchmark]

    args = ba.benchmark_args[benchmark]
    sub_email = 'submit.notifications@gmail.com'
    out_file_name = 'generated_run_' + benchmark.replace(' ', '_') + '_vanilla.sh'
    util.shell('sed -e "s;SUBMAIL;' + sub_email + ';g" -e "s;BENCHMARK;' + benchmark
               + ';g" -e "s;FLAVOR;vanilla;g" -e "s;INVOK;' + args + ';g" '
               + ba.template_file + ' > ' + out_file_name, dry=True)
    return out_file_name
