import { Component } from 'react';
import Dexie from 'dexie'

class Cache extends Component {
  /**
   * A cache for the TranQL web app using the IndexedDB client DB.
   */
  constructor(props) {
    /* Create state elements and initialize configuration. */
    super(props);
    this.db = new Dexie('TranQLClientCache');
    // Declare tables, IDs and indexes
    this.db.version(1).stores({
      cache: '++id, name, &key, graph'
    });
    this.write = this.write.bind (this);
  }
  async write (data) {//key, data) {
    // Write cache.
    return await this.db.cache.put (data);
  }
  async read (key) {
    return await this.db.cache 
    .where('key')
    .equals (key)
    .toArray();
  }
  async get (id, callback) {
    return await this.db.cache.get (id, callback);
  }
  async clear () {
    return await this.db.cache.clear ();
  }
}

export default Cache;
