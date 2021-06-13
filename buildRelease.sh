#!/bin/bash
(cd ../../; python2 ./generator.pyc hs_modbusTCP_writer utf-8)
markdown2 --extras tables,fenced-code-blocks,strike,target-blank-links doc/log14185.md > release/log14185.html
(cd release; zip -r 14185_hs_modbusTCP_writer.hslz *)
