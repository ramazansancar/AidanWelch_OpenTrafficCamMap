'use strict';
const fs = require( 'fs' );
const https = require( 'https' );

const cameras = JSON.parse( fs.readFileSync( '../cameras/USA.json' ) );

https.request( 'https://www.511virginia.org/data/geojson/icons.cameras.geojson', ( res ) => {
	let data = '';

	res.on( 'data', ( chunk ) => {
		data += chunk;
	});

	res.on( 'end', () => {
		compile( JSON.parse( data ) );
	});
}).end();

class Camera {
	constructor ( cam ) {
		this.location = {
			description: cam.properties.description,
			direction: ( () => {
				switch ( cam.properties.direction ) {
				case 'NB':
					return 'North';
				case 'SB':
					return 'South';
				case 'EB':
					return 'East';
				case 'WB':
					return 'West';
				}
			})(),
			latitude: parseFloat( cam.geometry.coordinates[1] ),
			longitude: parseFloat( cam.geometry.coordinates[0] )
		};
		this.url = cam.properties.ios_url;
		this.encoding = 'H.264';
		this.format = 'M3U8';
		this.markedForReview = false;
	}
}

function compile ( data ) {
	if ( !cameras.Virginia ) {
		cameras.Virginia = {};
	}

	for ( const cam of data.features ) {
		if ( cam.properties.jurisdiction !== null ) {
			if ( !cameras.Virginia[cam.properties.jurisdiction] ) {
				cameras.Virginia[cam.properties.jurisdiction] = [];
			}

			cameras.Virginia[cam.properties.jurisdiction].push( new Camera( cam ) );
		} else {
			if ( !cameras.Virginia.other ) {
				cameras.Virginia.other = [];
			}

			cameras.Virginia.other.push( new Camera( cam ) );
		}
	}

	fs.writeFileSync( '../cameras/USA.json', JSON.stringify( cameras, null, 2 ) );
}