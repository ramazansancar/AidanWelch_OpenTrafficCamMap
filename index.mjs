import { readFileSync, writeFileSync } from 'fs';
import compileUSA from './compilation/USA/index.mjs';
import { fileURLToPath } from 'url';
import path from 'path';

const dir = path.dirname( fileURLToPath( import.meta.url ) );

compileUSA().then( res => {
	const camPath = path.join( dir, 'cameras', 'USA.json' );
	const oldCameras = JSON.parse( readFileSync( camPath ) );
	for ( const state in { ...oldCameras, ...res }) {
		let difference = 0;
		if ( state in res ) {
			for ( const county in res[state] ) {
				difference += res[state][county].length;
			}
		}

		if ( state in oldCameras ) {
			for ( const county in oldCameras[state] ) {
				difference -= oldCameras[state][county].length;
			}
		}

		console.info(
			`${state} has ${( difference < 0 ) ? 'lost' : 'gained'} ${Math.abs( difference )} cameras`
		);
	}

	writeFileSync( camPath, JSON.stringify( res ) );
});